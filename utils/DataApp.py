import os
from pathlib import Path
from tempfile import NamedTemporaryFile


class DataApp:
    def __init__(self, label_path):
        self.label_path = Path(label_path)
        self.data = []
        self.load_data_from_path(self.label_path)

    def load_data_from_path(self, label_path):
        with open(label_path, encoding='utf-8') as file:
            contexts = file.readlines()

        for line_number, line in enumerate(contexts, start=1):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 5:
                raise ValueError(f'{label_path}:{line_number} 应包含 5 个字段，实际为 {len(parts)} 个')
            try:
                context = [float(value) for value in parts]
            except ValueError as exc:
                raise ValueError(f'{label_path}:{line_number} 包含非数字字段') from exc
            class_id = context[0]
            if not class_id.is_integer() or class_id < 0:
                raise ValueError(f'{label_path}:{line_number} 的类别 ID 无效: {class_id}')
            if any(not 0 <= value <= 1 for value in context[1:]):
                raise ValueError(f'{label_path}:{line_number} 的归一化坐标必须位于 [0, 1]')
            context[0] = int(class_id)
            self.data.append(context)

    @staticmethod
    def _validate(data):
        if len(data) != 5:
            raise ValueError('检测标签必须包含类别和 4 个坐标')
        class_id, *coordinates = data
        if int(class_id) != class_id or class_id < 0:
            raise ValueError(f'类别 ID 无效: {class_id}')
        if any(not 0 <= float(value) <= 1 for value in coordinates):
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

    def save(self, dot=3):
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
