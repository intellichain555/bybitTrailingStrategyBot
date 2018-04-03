from enum import Enum


class Value:
    class Type(Enum):
        ABS = 0
        REL = 1

    def __init__(self, obj: str):
        if not isinstance(obj, str):
            obj = str(obj)
        if obj.endswith('%'):
            self.type = Value.Type.REL
        else:
            self.type = Value.Type.ABS

        self.v = float(obj.replace('%', ''))

    def is_abs(self):
        return self.type == Value.Type.ABS

    def is_rel(self):
        return self.type == Value.Type.REL

    def get_val(self, rel_val):
        if self.is_abs():
            return self.v
        return round(rel_val * self.v / 100, 8)

    def __str__(self):
        return '{:.2f}%'.format(self.v) if self.is_rel() else '{:.8f}'.format(self.v)

    def __repr__(self):
        return self.__str__()
