from cassowary import SimplexSolver, Variable, REQUIRED, STRONG, WEAK, MEDIUM

# divide by (max number of tiles across all rows) maybe + 1

# 1 {{{

solver = SimplexSolver()

x1 = Variable("x1")
x2 = Variable("x2")
x3 = Variable("x3")
x4 = Variable("x4")
xs = (x1, x2, x3, x4)

width = 800

# width = Variable("width", 800)
# solver.add_stay(width, REQUIRED)

for x in xs:
    solver.add_constraint(x >= 1)
    solver.add_constraint(x < width)
    solver.add_constraint(x >= (width // 3))

solver.add_constraint(x1 + x2 + x3 == width)
solver.add_constraint(x1 + x4 == width)

print(x1, x2, x3, x4, width)

# }}} 1

# 2 {{{

solver = SimplexSolver()

x1 = Variable("x1")
x2 = Variable("x2")
x3 = Variable("x3")
x4 = Variable("x4")
x5 = Variable("x5")
xs = (x1, x2, x3, x4, x5)

width = 800

# width = Variable("width", 800)
# solver.add_stay(width, REQUIRED)

for x in xs:
    solver.add_constraint(x >= 1)
    solver.add_constraint(x < width)
    solver.add_constraint(x >= (width // 3))

solver.add_constraint(x1 + x2 == width)
solver.add_constraint(x1 + x3 + x4 == width)
solver.add_constraint(x5 + x4 == width)

print(x1, x2, x3, x4, x5, width)

# }}} 2
