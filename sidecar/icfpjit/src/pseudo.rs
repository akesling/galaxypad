use std::collections::HashMap;
use std::rc::Rc;

// See video course https://icfpcontest2020.github.io/#/post/2054

trait Expr {
    fn evaluated(&self) -> &Option<Rc<dyn Expr>>;
}

#[derive(Default)]
struct Atom {
    _evaluated: Option<Rc<dyn Expr>>,

    name: String,
}

impl Expr for Atom {
    fn evaluated(&self) -> &Option<Rc<dyn Expr>> {
        return &self._evaluated;
    }
}

impl Expr for &Atom {
    fn evaluated(&self) -> &Option<Rc<dyn Expr>> {
        return &self._evaluated;
    }
}

#[derive(Default)]
struct Ap {
    _evaluated: Option<Rc<dyn Expr>>,

    func: Option<Rc<dyn Expr>>,
    arg: Option<Rc<dyn Expr>>,
}

impl Expr for Ap {
    fn evaluated(&self) -> &Option<Rc<dyn Expr>> {
        return &self._evaluated;
    }
}

impl Expr for &Ap {
    fn evaluated(&self) -> &Option<Rc<dyn Expr>> {
        return &self._evaluated;
    }
}

#[derive(Default)]
struct Vec {
    x: u64,
    y: u64,
}

fn parse_functions(script_string: &str) -> HashMap<String, Rc<dyn Expr>> {
    panic!("Parse functions is not yet implemented");
    return HashMap::new();
}

fn main() {
    let CONS: Rc<dyn Expr> = Rc::new(Atom{name: "cons".to_owned(), _evaluated: None});
    let T: Rc<dyn Expr> = Rc::new(Atom{name: "t".to_owned(), _evaluated: None});
    let F: Rc<dyn Expr> = Rc::new(Atom{name: "f".to_owned(), _evaluated: None});
    let NIL: Rc<dyn Expr> = Rc::new(Atom{name: "nil".to_owned(), _evaluated: None});

    let functions = parse_functions("DUMMY VALUE");

    // See https://message-from-space.readthedocs.io/en/latest/message39.html
    let state: Rc<dyn Expr> = NIL;
    let vector = Vec{ x: 0, y: 0};

    loop {
        let mut click = Ap{
            func: Some(Rc::new(Ap{
                func: Some(CONS.clone()),
                arg: Some(Rc::new(Atom {name: vector.x.to_string(), ..Default::default()})),
                ..Default::default()
            })),
            arg: Some(Rc::new(Atom{name: vector.y.to_string(), ..Default::default()})),
            ..Default::default()
        };
//        var (newState, images) = interact(state, click)
//        PRINT_IMAGES(images)
//        vector = REQUEST_CLICK_FROM_USER()
//        state = newState
    }

// // See https://message-from-space.readthedocs.io/en/latest/message38.html
// (Expr, Expr) interact(Expr state, Expr event)
//     Expr expr = Ap(Ap(Atom("galaxy"), state), event)
//     Expr res = eval(expr)
//     // Note: res will be modulatable here (consists of cons, nil and numbers only)
//     var [flag, newState, data] = GET_LIST_ITEMS_FROM_EXPR(res)
//     if (asNum(flag) == 0)
//         return (newState, data)
//     return interact(newState, SEND_TO_ALIEN_PROXY(data))
// 
// Expr eval(Expr expr)
//     if (expr.Evaluated != null)
//         return expr.Evaluated
//     Expr initialExpr = expr
//     while (true)
//         Expr result = tryEval(expr)
//         if (result == expr)
//             initialExpr.Evaluated = result
//             return result
//         expr = result
// 
// Expr tryEval(Expr expr)
//     if (expr.Evaluated != null)
//         return expr.Evaluated
//     if (expr is Atom && functions[expr.Name] != null)
//         return functions[expr.Name]
//     if (expr is Ap)
//         Expr fun = eval(expr.Fun)
//         Expr x = expr.Arg
//         if (fun is Atom)
//             if (fun.Name == "neg") return Atom(-asNum(eval(x)))
//             if (fun.Name == "i") return x
//             if (fun.Name == "nil") return t
//             if (fun.Name == "isnil") return Ap(x, Ap(t, Ap(t, f)))
//             if (fun.Name == "car") return Ap(x, t)
//             if (fun.Name == "cdr") return Ap(x, f)
//         if (fun is Ap)
//             Expr fun2 = eval(fun.Fun)
//             Expr y = fun.Arg
//             if (fun2 is Atom)
//                 if (fun2.Name == "t") return y
//                 if (fun2.Name == "f") return x
//                 if (fun2.Name == "add") return Atom(asNum(eval(x)) + asNum(eval(y)))
//                 if (fun2.Name == "mul") return Atom(asNum(eval(x)) * asNum(eval(y)))
//                 if (fun2.Name == "div") return Atom(asNum(eval(y)) / asNum(eval(x)))
//                 if (fun2.Name == "lt") return asNum(eval(y)) < asNum(eval(x)) ? t : f
//                 if (fun2.Name == "eq") return asNum(eval(x)) == asNum(eval(y)) ? t : f
//                 if (fun2.Name == "cons") return evalCons(y, x)
//             if (fun2 is Ap)
//                 Expr fun3 = eval(fun2.Fun)
//                 Expr z = fun2.Arg
//                 if (fun3 is Atom)
//                     if (fun3.Name == "s") return Ap(Ap(z, x), Ap(y, x))
//                     if (fun3.Name == "c") return Ap(Ap(z, x), y)
//                     if (fun3.Name == "b") return Ap(z, Ap(y, x))
//                     if (fun3.Name == "cons") return Ap(Ap(x, z), y)
//     return expr
// 
// 
// Expr evalCons(Expr a, Expr b)
//     Expr res = Ap(Ap(cons, eval(a)), eval(b))
//     res.Evaluated = res
//     return res
// 
// number asNum(Expr n)
//     if (n is Atom)
//         return PARSE_NUMBER(n.Name)
//     ERROR("not a number")
}

#[cfg(test)]
mod tests {
    #[test]
    fn pseudo_it_works() {
        assert_eq!(2 + 2, 4);
    }
}
