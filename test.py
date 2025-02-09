class Person:
    def __init__(self, fname, lname):
        self.firstname = fname
        self.lastname = lname

    def printname(self):
        print(self.firstname, self.lastname)

class Job:
    def __init__(self, job):
        self.job = job

    def printjob(self):
        print(self.job)

class Employed(Person,Job):
    def __init__(self, fname, lname, job):
        Person.__init__(self, fname, lname)
        Job.__init__(self, job)

    def report(self):
        print("Name:", self.printname)
        print("Job:", self.printjob)

x = Employed("John", "Doe", "Agent")
x.report()