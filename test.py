from injector import Injector, inject


class A:
    name = "A"


@inject
class B:
    def __init__(self, a: A):
        self.a = a

    def get_name(self):
        return self.a.name

    def print_name(self):
        print(self.get_name())


injector = Injector()

b = injector.get(B)
b.print_name()
