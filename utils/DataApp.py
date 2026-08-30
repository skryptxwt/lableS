import os
from pathlib import Path
from tempfile import NamedTemporaryFile


class DataApp:
    TASKS = ('detect', 'segment', 'obb', 'pose')

    def __init__(self, label_path, task='detect', kpt_shape=(17, 3)):
        self.label_path = Path(label_path)
        if task not in self.TASKS:
            raise ValueError(f'不支持的标注任务: {task}')
        self.task = task
        self.kpt_shape = self._normalize_kpt_shape(kpt_shape)
        self.data = []
        self.load_data_from_path(self.label_path)

    @staticmethod
    def _normalize_kpt_shape(value):
        try:
            count, dimensions = int(value[0]), int(value[1])
        except (TypeError, ValueError, IndexError):
            raise ValueError('kpt_shape 必须是 [关键点数量, 2或3]')
        if count < 1 or dimensions not in (2, 3):
            raise ValueError('kpt_shape 必须是 [关键点数量, 2或3]')
        return count, dimensions

    def load_data_from_path(self, label_path):
        with open(label_path, encoding='utf-8') as file:
            contexts = file.readlines()

        for line_number, line in enumerate(contexts, start=1):
            if not line.strip():
                continue
            parts = line.split()
            try:
                context = [float(value) for value in parts]
            except ValueError as exc:
                raise ValueError(f'{label_path}:{line_number} 包含非数字字段') from exc
            try:
                self._validate(context)
            except ValueError as exc:
                raise ValueError(f'{label_path}:{line_number} {exc}') from exc
            context[0] = int(context[0])
            self.data.append(context)

    def _validate(self, data):
        lengths = {
            'detect': 5,
            'obb': 9,
            'pose': 5 + self.kpt_shape[0] * self.kpt_shape[1],
        }
        if self.task in lengths and len(data) != lengths[self.task]:
            raise ValueError(
                f'{self.task} 标签应包含 {lengths[self.task]} 个字段，实际为 {len(data)} 个')
        if self.task == 'segment' and (len(data) < 7 or (len(data) - 1) % 2):
            raise ValueError('segment 标签至少需要 3 个点，坐标必须成对出现')
        class_id, *coordinates = data
        try:
            class_value = float(class_id)
        except (TypeError, ValueError):
            raise ValueError(f'类别 ID 无效: {class_id}')
        if not class_value.is_integer() or class_value < 0:
            raise ValueError(f'类别 ID 无效: {class_id}')
        if self.task == 'pose':
            box = coordinates[:4]
            points = coordinates[4:]
            if any(not 0 <= float(value) <= 1 for value in box):
                raise ValueError('边界框归一化坐标必须位于 [0, 1]')
            dimensions = self.kpt_shape[1]
            for offset in range(0, len(points), dimensions):
                point = points[offset:offset + dimensions]
                if any(not 0 <= float(value) <= 1 for value in point[:2]):
                    raise ValueError('关键点归一化坐标必须位于 [0, 1]')
                if dimensions == 3 and float(point[2]) not in (0, 1, 2):
                    raise ValueError('关键点可见性必须为 0、1 或 2')
        elif any(not 0 <= float(value) <= 1 for value in coordinates):
            raise ValueError('归一化坐标必须位于 [0, 1]')

    def append(self, data):
        self._validate(data)
        self.data.append(list(data))

    def insert(self, index, data):
        self._validate(data)
        self.data.insert(index, list(data))

    def pop(self, index):
        self.data.pop(index)

    def merge(self, other):
        """Append labels not already present and return the number added."""
        known = {tuple(label) for label in self.data}
        added = 0
        for label in other:
            key = tuple(label)
            if key in known:
                continue
            self.append(label)
            known.add(key)
            added += 1
        return added

    def save(self, dot=None):
        if dot is None:
            dot = 3 if self.task == 'detect' else 6
        lines = []
        for class_id, *coordinates in self.data:
            values = [str(int(class_id)), *(str(round(float(value), dot)) for value in coordinates)]
            lines.append(' '.join(values))
        text = '\n'.join(lines)

        self.label_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with NamedTemporaryFile(
                    mode='w', encoding='utf-8', dir=self.label_path.parent,
                    prefix=f'.{self.label_path.name}.', suffix='.tmp', delete=False) as file:
                file.write(text)
                file.flush()
                os.fsync(file.fileno())
                temp_path = Path(file.name)
            os.replace(temp_path, self.label_path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

    def __setitem__(self, key, value):
        self._validate(value)
        self.data[key] = list(value)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        yield from self.data

    def __repr__(self):
        return str(self.data)
