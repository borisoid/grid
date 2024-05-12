from kiwisolver import Solver, Variable


solver = Solver()

x1 = Variable("x1")
x2 = Variable("x2")
x3 = Variable("x3")
x4 = Variable("x4")
x5 = Variable("x5")
xs = (x1, x2, x3, x4, x5)

width = 800

# width = Variable("width")
# solver.addConstraint((width == 800) | "required")

for x in xs:
    solver.addConstraint(x >= 1)
    solver.addConstraint(x <= (width - 1))
    solver.addConstraint(x >= (width // 3))

solver.addConstraint(x1 + x2 == width)
solver.addConstraint(x1 + x3 + x4 == width)
solver.addConstraint(x5 + x4 == width)

solver.updateVariables()

print(x1.value(), x2.value(), x3.value(), x4.value(), x5.value(), width)
# print(x1.value(), x2.value(), x3.value(), x4.value(), x5.value(), width.value())
