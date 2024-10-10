from operator import add, sub, mul, neg

from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
from element import Element


class Interpreter(InterpreterBase):
    BIN_OPS = {
        "+": add,
        "-": sub,
        "*": mul,
    }
    UNARY_OPS = {
        "neg": neg
    }

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output

    def run(self, program: str):
        ast: Element = parse_program(program)
        if ast.elem_type != super().PROGRAM_NODE:
            raise ValueError("bad node type")

        self.vars = {}
        self.funcs = {}
        for f in ast.get("functions"):
            if f in self.funcs:
                self.error(ErrorType.FAULT_ERROR, "you can't have multiple function defns")
            self.funcs[f.get("name")] = f

        if "main" not in self.funcs:
            self.error(ErrorType.NAME_ERROR, "No main function found.")

        self.run_func(self.funcs["main"])

    def run_func(self, func: Element):
        if func.elem_type != super().FUNC_NODE:
            raise ValueError("bad node type")

        for stmt in func.get("statements"):
            self.run_stmt(stmt)

    def run_stmt(self, stmt: Element):
        if stmt.elem_type == super().VAR_DEF_NODE:
            self.run_var_def(stmt)
        elif stmt.elem_type == "=":  # WHY IS THERE NO CONSTANT FOR THIS WHAT
            self.run_var_assign(stmt)
        elif stmt.elem_type == super().FCALL_NODE:
            self.run_fcall(stmt)
        else:
            raise ValueError("node isn't a statement")

    def run_var_def(self, var: Element):
        if var.elem_type != super().VAR_DEF_NODE:
            raise ValueError("node isn't a variable definition")

        name = var.get("name")
        if name in self.vars:
            self.error(ErrorType.NAME_ERROR, f"Variable {name} is already defined")
        self.vars[name] = None

    def run_var_assign(self, assign: Element):
        if assign.elem_type != "=":
            raise ValueError("node isn't a variable assignment")

        name = assign.get("name")
        if name not in self.vars:
            self.error(
                ErrorType.NAME_ERROR, f"Variable {name} hasn't been declared yet."
            )

        self.vars[name] = self.eval_expr(assign.get("expression"))

    def run_fcall(self, fcall: Element):
        if fcall.elem_type != super().FCALL_NODE:
            raise ValueError("node isn't a function call")

        name = fcall.get("name")
        args = fcall.get("args")
        if name == "print":
            to_output = [str(self.eval_expr(e)) for e in args]
            self.output("".join(to_output))
        elif name == "inputi":
            if len(args) > 0:
                prompt = [str(self.eval_expr(e)) for e in args]
                self.output("".join(prompt))
            return int(self.get_input())
        else:
            if name not in self.funcs:
                self.error(ErrorType.NAME_ERROR, f"Function {name} isn't supported")
            self.run_func(self.funcs[name])

    def eval_expr(self, expr: Element):
        if expr.elem_type in self.BIN_OPS:
            func = self.BIN_OPS[expr.elem_type]
            op1 = self.eval_expr(expr.get("op1"))
            op2 = self.eval_expr(expr.get("op2"))

            if type(op1) != type(op2):
                self.error(
                    ErrorType.TYPE_ERROR,
                    f"can't combine types of {type(op1)} and {type(op2)}",
                )
            return func(op1, op2)

        elif expr.elem_type in self.UNARY_OPS:
            func = self.UNARY_OPS[expr.elem_type]
            op = self.eval_expr(expr.get("op1"))
            return func(op)


        elif expr.elem_type == "-":
            return self.eval_expr(expr.get("op1")) - self.eval_expr(expr.get("op2"))

        elif expr.elem_type == super().INT_NODE:
            return expr.get("val")

        elif expr.elem_type == super().STRING_NODE:
            return expr.get("val")

        elif expr.elem_type == super().VAR_NODE:
            name = expr.get("name")
            if name not in self.vars:
                self.error(ErrorType.NAME_ERROR, f"Variable {name} doesn't exist")
            return self.vars[name]

        elif expr.elem_type == super().FCALL_NODE:
            return self.run_fcall(expr)

        else:
            raise ValueError("node isn't an expression")


if __name__ == "__main__":
    src = """func main() {  /* a function that computes the sum of two numbers */
  var first;
  var second;
  first = -5;
  first = inputi("Enter a first #: ");
  second = inputi("Enter a second #: ");
  var sum;
  sum = (first + second);   
  print("The sum is ", sum, "!");
  bruh();
}

func bruh() {
    print("YOASDOPFIJASPODIFJASD");
}
"""
    interp = Interpreter()
    interp.run(src)
