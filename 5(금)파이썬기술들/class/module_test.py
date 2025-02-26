class Calc:
    def __init__(self):
        self.first = 0
        self.second = 0 

    def set_num(self,first,second):
        self.first = first
        self.second = second

    def add(self):
        return self.first+self.second
    
    def print_message(self):
        if self.first==0:
            print("Hello")
        else:
            print('안Hello')