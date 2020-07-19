#include <stdio.h>

#include <string>
#include <vector>
#include <functional>
#include <iostream>
#include <unordered_map>
#include <unordered_set>
#include <fstream>

#include <algorithm> 
#include <cctype>
#include <locale>

// Routines to trim leading and trailing spaces taken from SO, they should
// really have these in the std lib...
//
// trim from start (in place)
static inline void ltrim(std::string &s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](int ch) {
        return !std::isspace(ch);
    }));
}

// trim from end (in place)
static inline void rtrim(std::string &s) {
    s.erase(std::find_if(s.rbegin(), s.rend(), [](int ch) {
        return !std::isspace(ch);
    }).base(), s.end());
}

// trim from both ends (in place)
static inline void trim(std::string &s) {
    ltrim(s);
    rtrim(s);
}

// String splitting routine take from SO and modified for trimming spaces.
std::vector<std::string> split (const std::string& s, const std::string& delimiter) {
    size_t pos_start = 0;
    size_t pos_end;
    size_t delim_len = delimiter.length();
    std::string token;
    std::vector<std::string> res;

    while ((pos_end = s.find (delimiter, pos_start)) != std::string::npos) {
        token = s.substr(pos_start, pos_end - pos_start);
        pos_start = pos_end + delim_len;
        res.push_back(token);
    }

    res.push_back(s.substr(pos_start));

    // lol just go agane on everything to trim it
    for (std::string& str : res) {
      trim(str);
    }
    return res;
}

// Tests whether the given string is an integer
inline bool IsInteger(const std::string & s) {
   if(s.empty() || ((!isdigit(s[0])) && (s[0] != '-') && (s[0] != '+'))) return false;

   char * p;
   strtol(s.c_str(), &p, 10);

   return (*p == 0);
}

// Panic routines blow up the program if something unexpected happens. Fuck
// exceptions
void panic(const std::string& msg) {
  std::cerr << msg << std::endl;
  exit(-1);
}

void panic_if(bool should_panic, const std::string& msg) {
  if (!should_panic) {
    return;
  }
  std::cerr << msg << std::endl;
  exit(-1);
}

// An ExprReg right now is an int that is the index of the Expr in oour Expr
// pool. Later we might change this if we store the Exprs in a different way to
// refcount and recycle them.
using ExprRef = int;
constexpr ExprRef noexpr = -1;

// Tells you wtf this Expr is.
constexpr int kAtomFlag = 0x1;
constexpr int kApFlag = 0x2;

// An Expr is a basic node in our tree. Depending on the type it will have
// different fields set, some if it is an Ap, others if it is an Atom. It also
// caches its evauluated form, I guess to prevent infinite recursion or speed it
// up or something.
struct Expr {
  int flags;
	ExprRef evaluated;

  // Only if Atom
	std::string name;

  // Only if Ap
	ExprRef func;
	ExprRef arg;

  // This is invoked when we add a new Expr to the Expr pool, making sure it
  // starts in a sane state, mainly making sure evaluated is set to "nullptr"
  // (noexpr for us).
  Expr() {
    flags = 0;
    evaluated = noexpr;
  }

};

// These helpers help us figure out what is stored in a given Expr
inline bool IsAtom(const Expr& e) {
  return (e.flags & kAtomFlag) != 0;
}

inline bool IsAp(const Expr& e) {
  return (e.flags & kApFlag) != 0;
}

// This helper converts an Atom to an Int. If it's not an Atom that can be
// represented as an int it DESTROYS EVERYTHING.
inline int AsNum(const Expr& e) {
  if (!IsInteger(e.name)) {
    panic("tried to nummify " + e.name);
  }

 char* p;
 return strtol(e.name.c_str(), &p, 10);
}

// This Vec is used to hold mouse clicks in the pseudocode, we might not need
// it.
struct Vec {
	int x;
  int y;
};

// Used for serializaiton.
const std::unordered_set<std::string> g_atoms = {
    "add",
    "inc",
    "dec",
    "i",
    "t",
    "f",
    "mul",
    "div",
    "eq",
    "lt",
    "neg",
    "s",
    "c",
    "b",
    "pwr2",
    "cons",
    "car",
    "cdr",
    "nil",
    "isnil",
    "vec",
    "if0",
    "send",
    "checkerboard",
    "draw",
    "multipledraw",
    "modem",
    "f38",
    "statelessdraw",
    "interact",
};

// The engine does the heavy lifting. It maintains the pool of Exprs and allows
// easy construction of Ap and Atoms, as well as parses and loads function
// replacements from a file (galaxy.txt mainly).
class Engine {
 public:
  Engine(int initial_slots) {
    // To speed things up we reserve space for a few Exprs off the bat.
    exprs_.reserve(initial_slots);

    // These are a few handy Exprs to have pre defined, we use them a lot during
    // Eval.
    cons_ = Atom("cons");
    t_ = Atom("t");
    f_ = Atom("f");
    nil_ = Atom("nil");
  }

  // Gets the Expr given a reference. Important abstraction to have 
  const Expr& deref(ExprRef e) const {
    return exprs_[e];
  }
  Expr& deref(ExprRef e) {
    return exprs_[e];
  }


  // Create a new Expr and return the reference
  ExprRef NewExpr() {
    const int pos = exprs_.size();
    exprs_.emplace_back();
    return pos;
  }

  // Create a new Atom Expr with the given name
  ExprRef Atom(const std::string& name) {
    const auto a = NewExpr();
    auto& e = deref(a);
    e.flags = kAtomFlag;
    e.name = name;
    return a;
  }

  // Create a new Atom Expr with the given number set as the name
  ExprRef Atom(int n) {
    const auto a = NewExpr();
    auto& e = deref(a);
    e.flags = kAtomFlag;
    e.name = std::to_string(n);
    return a;
  }

  // Create a new Ap Expr using the given refs to the function and arg Exprs
  ExprRef Ap(ExprRef func, ExprRef arg) {
    const auto ap = NewExpr();
    auto& e = deref(ap);
    e.flags = kApFlag;
    e.func = func;
    e.arg = arg;
    return ap;
  }

  // Looks up the given Expr and converts the name to a number, blows up if it's
  // not an Atom with name as a parseable int.
  int AsNum(ExprRef ref) const {
    return ::AsNum(deref(ref));
  }

  // Recursively looks up and converts the given reference to a string format
  // for debugging
  std::string ExprToString(ExprRef ref) const {
    const auto& expr = deref(ref);
    if (IsAp(expr)) {
      return "Ap(" + ExprToString(expr.func) + "," + ExprToString(expr.arg) +
      ")";
    }
    if (IsAtom(expr)) {
      return expr.name;
    }
    panic("unsure how to print " + expr.name);
    return "???";
  }

  // Deserialization returns an ExprRef and a "tail" which we just say is the
  // position of the next token in the vector of tokens.
	struct DeserializeResult {
		size_t pos;
		ExprRef expr;
	};

  // Takes a list of tokens and a current position and recursively pops tokens
  // from the token list and converts them to Exprs, allocating from the pool as
  // needed.
  DeserializeResult Deserialize(size_t pos, const std::vector<std::string>& expr) {
    const auto& str = expr[pos];
    std::cout << "deserialize " << pos << ": " << str << std::endl;
    if (str == "ap") {
      auto result_left = Deserialize(++pos, expr);
      auto result_right = Deserialize(result_left.pos, expr);
      const ExprRef ap_expr = Ap(result_left.expr, result_right.expr);
      return {result_right.pos, ap_expr};
    }

    if (g_atoms.count(str) != 0) {
      return {++pos, Atom(str)};
    }

    if (IsInteger(str)) {
      return {++pos, Atom(str)};
    }

    // This just makes an atom out of a function reference which we'll later
    // look up in the eval. We handle this by testing each Atom to see if it is
    // in the list of loaded functions.
    if (str[0] == ':') {
      return {++pos, Atom(str)};
    }

    panic("could not deserialize: " + str);
    return {};
  }

  // Loads a function definition, which must be of the form:
  // <name> = <body expr>
  void LoadFunc(const std::string& line) {
    const auto fsplit = split(line, "=");
    panic_if(fsplit.size() != 2, "Could not split function by =");
    std::cout << "func (" << fsplit[0] << "," << fsplit[1] << ")" << std::endl;

    // TODO(myenik): No sanity checking on the name being just a single token
		const auto fname = fsplit[0];
		const auto body = fsplit[1];
		auto body_split = split(fsplit[1], " ");
		const auto result = Deserialize(0, body_split);

    // Ensure we actually parsed the entire body expression and store the
    // resulting function body for replacement during Eval.
    panic_if(result.pos != body_split.size(), "didn't reach end of body parsing");
		funcs_[fname] = result.expr;
  }

  // Opens the given filename and attempts to load each line as a function
  // definition (pretty much just for galaxy.txt)
  void LoadFuncs(const std::string& filename) {
    std::ifstream file(filename);
    std::string line;
    while(std::getline(file, line)) {
      std::cout << "loading: " << line << std::endl;
      LoadFunc(line);
    }
  }

  // Dumps info about loaded functions.
  void Dump() {
    for (const auto func : funcs_) {
      std::cout << func.first << " = " << ExprToString(func.second) << std::endl;
    }
    std::cout << "galaxy" << " = " << ExprToString(funcs_[std::string("galaxy")]) << std::endl;
  }

  // Eval loop from pseudocode
  ExprRef Eval(ExprRef ref) {
    auto& expr = deref(ref);
    if (expr.evaluated != noexpr) {
      std::cout << "Eval cached ref " << ref << std::endl;
      return expr.evaluated;
    }

    ExprRef initial_ref = ref;
    ExprRef current_ref = ref;
    while (true) {
      ExprRef result = TryEval(current_ref);
      if (result == current_ref) {
        deref(initial_ref).evaluated = result;
        return result;
      }
      current_ref = result;
    }
  }

  // TryEval from pseudocode
  ExprRef TryEval(ExprRef ref) {
    const auto& expr = deref(ref);
    if (expr.evaluated != noexpr) {
      std::cout << "TryEval cached ref " << ref << std::endl;
      return expr.evaluated;
    }

    std::cout << "TryEval func test " << expr.name << std::endl;
    if (IsAtom(expr) && funcs_.count(expr.name) != 0) {
      std::cout << "TryEval ref is func " << ref << std::endl;
      return funcs_[expr.name];
    }

    if (IsAp(expr)) {
      std::cout << "TryEval ref is Ap " << ref << std::endl;
      const auto func_ref = Eval(expr.func);
      const auto x_ref = expr.arg;

      const auto& func = deref(func_ref);
      if (IsAtom(func)) {
        if (func.name == "neg") {
          return Atom(-AsNum(Eval(x_ref)));
        }
        if (func.name == "i") {
          return x_ref;
        }
        if (func.name == "nil") {
          return t_;
        }
        if (func.name == "isnil") {
          return Ap(x_ref, Ap(t_, Ap(t_, f_)));
        }
        if (func.name == "car") {
          return Ap(x_ref, t_);
        }
        if (func.name == "cdr") {
          return Ap(x_ref, f_);
        }
      }
      if (IsAp(func)) {
        const ExprRef y_ref = func.arg;
        //const ExprRef func2_ref = Eval(func_ref);
        const ExprRef func2_ref = Eval(func.func);
        const Expr& func2 = deref(func2_ref);
        if (IsAtom(func2)) {
          if (func2.name == "t") {
            return y_ref;
          }
          if (func2.name == "f") {
            return x_ref;
          }
          if (func2.name == "add") {
            return Atom(AsNum(Eval(x_ref)) + AsNum(Eval(y_ref)));
          }
          if (func2.name == "mul") {
            return Atom(AsNum(Eval(x_ref)) * AsNum(Eval(y_ref)));
          }
          if (func2.name == "div") {
            return Atom(AsNum(Eval(x_ref)) / AsNum(Eval(y_ref)));
          }
          if (func2.name == "lt") {
            return AsNum(Eval(x_ref)) < AsNum(Eval(y_ref)) ? t_ : f_;
          }
          if (func2.name == "eq") {
            return AsNum(Eval(x_ref)) == AsNum(Eval(y_ref)) ? t_ : f_;
          }
          if (func2.name == "cons") {
            return EvalCons(y_ref, x_ref);
          }
        }
        if (IsAp(func2)) {
          const ExprRef z_ref = func2.arg;
          const ExprRef func3_ref = Eval(func2.func);
          const Expr& func3 = deref(func3_ref);
          if (IsAtom(func3)) {
            if (func3.name == "s") {
              return Ap(Ap(z_ref, x_ref), Ap(y_ref, x_ref));
            }
            if (func3.name == "c") {
              return Ap(Ap(z_ref, x_ref), y_ref);
            }
            if (func3.name == "b") {
              return Ap(Ap(x_ref, z_ref), y_ref);
            }
            if (func3.name == "cons") {
              return Ap(Ap(x_ref, z_ref), y_ref);
            }
          }
        }
      }
    }

    std::cout << "hmmm" << std::endl;
    return ref;
  }

  // Also from pseudocode
  ExprRef EvalCons(ExprRef a, ExprRef b) {
    const ExprRef res = Ap(Ap(cons_, Eval(a)), Eval(b));
    deref(res).evaluated = res;
    return res;
  }

  //std::vector<ExprRef> FlattenList(ExprRef ref, std::vector<ExprRef>& flattened) {
  //  const Expr& first = deref(ref);
  //  if (!IsAp(first)) {
  //    panic("failed parsing list");
  //  }

  //  const auto& second = deref(first.func);
  //  if (!IsAp(second)) {
  //    panic("failed parsing list");
  //  }
  //  return {};
  //}
  //
  //std::vector<ExprRef> FlattenList(ExprRef ref) {
  //}
  //
  //struct UnpackedProtocolResult {
  //  ExprRef flag;
  //  ExprRef new_state;
  //  ExprRef data;
  //};
  //
  // Unpacks triplet into result
  //UnpackedProtocolResult GetListItemsFromExpr(ExprRef ref) {
  //  UnpackedProtocolResult result;
  //}
  //
  //struct InteractResult {
  //  ExprRef data;
  //  ExprRef pics;
  //};
  //
  // Takes a state data blob, and event pixel.
  //
  // Returns a new data blob and a list of "pictures".
  //InteractResult InteractGalaxy(ExprRef state, ExprRef event) {
  //  ExprRef eref = Ap(Ap(Atom("galaxy"), state), event);
  //  ExprRef res = Eval(eref);
  //  
  //  // GET_LIST_ITEMS_FROM_EXPR(...)
  //  return {noexpr, noexpr};
  //}

  // Runs the first step of the galaxy protocol, just for debugging, will go
  // away soon...
  ExprRef TestOneStep() {
    auto state = nil_;
    ExprRef click = Ap(Ap(cons_, Atom(0)), Atom(0));

    ExprRef eref = Ap(Ap(Atom("galaxy"), state), click);
    ExprRef res = Eval(eref);
    return res;
  }

 private:
  ExprRef cons_;
  ExprRef t_;
  ExprRef f_;
  ExprRef nil_;

  // The Expr pool. Currently we don't recycle Exprs, they grow in an unbounded
  // fashion until we run out of memory. We can fix this if needed.
  std::vector<Expr> exprs_;

  // Map of function names to bodies that we use to substitute for the function
  // names during Eval.
  std::unordered_map<std::string, ExprRef> funcs_;
};

// Simple main test...
int main(int argc, char** argv) {
  if (argc != 2) {
    std::cerr << "usage: interp <galaxy.txt path>" << std::endl;
    return -1;
  }

  Engine engine(1000);
  engine.LoadFuncs(argv[1]);
  engine.Dump();

  // TEST AYY LMAO
  auto res = engine.TestOneStep();
  std::cout << "RESULT:" << std::endl << engine.ExprToString(res) << std::endl;
  return 0;
}
