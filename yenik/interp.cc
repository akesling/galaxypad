#include <stdio.h>

#include <string>
#include <vector>
#include <functional>
#include <iostream>
#include <iomanip>
#include <unordered_map>
#include <unordered_set>
#include <fstream>

#include <algorithm> 
#include <cctype>
#include <locale>

#include <SDL2/SDL.h>

#define WINDOW_WIDTH 1600
#define WINDOW_HEIGHT 800

const int kPixScale = 4;
const int kYOffset = WINDOW_HEIGHT/kPixScale/2 + 50;
const int kXOffset = WINDOW_WIDTH/kPixScale/2;

// We can enable and disable debug traces using a null stream.
class NullBuffer : public std::streambuf {
 public:
  int overflow(int c) { return c; }
};

NullBuffer null_buffer;
std::ostream null_stream(&null_buffer);

constexpr int kLogLevel = 0;

std::ostream& LogStream(int level) {
  return (level <= kLogLevel) ? std::cout : null_stream;
}

std::ostream& LogStream() {
  return LogStream(3);
}

#define GOTTA_GO_FAST 1
#define Log(__x) if (GOTTA_GO_FAST == 0) LogStream(__x)

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
inline long AsNum(const Expr& e) {
  if (IsInteger(e.name)) {
    char* p;
    return strtol(e.name.c_str(), &p, 10);
  }

  if (e.name == "t") {
    return 1;
  }
  if (e.name == "f") {
    return 0;
  }

  panic("cannot nummify " + e.name);
  return 0;
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
    //"inc",
    //"dec",
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
    //"pwr2",
    "cons",
    "car",
    "cdr",
    "nil",
    "isnil",
    //"vec",
    //"if0",
    //"send",
    //"checkerboard",
    //"draw",
    //"multipledraw",
    //"modem",
    //"f38",
    //"statelessdraw",
    //"interact",
};

// The engine does the heavy lifting. It maintains the pool of Exprs and allows
// easy construction of Ap and Atoms, as well as parses and loads function
// replacements from a file (galaxy.txt mainly).
class Engine {
 public:
  Engine(int initial_slots, SDL_Renderer* renderer) {
    // To speed things up we reserve space for a few Exprs off the bat.
    exprs_.reserve(initial_slots);

    // These are a few handy Exprs to have pre defined, we use them a lot during
    // Eval.
    cons_ = Atom("cons");
    t_ = Atom("t");
    f_ = Atom("f");
    nil_ = Atom("nil");

		renderer_ = renderer;
		
		//SDL_RenderDrawPoint(renderer, i, i);
		//SDL_RenderPresent(renderer);
  }

  // Gets the Expr given a reference. Important abstraction to have.
  //
  // IMPORTANT: the returned Expr& is invalidated by calls that allocate new (unrelated) Expr's. (e.g., Eval).
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
  long AsNum(ExprRef ref) const {
    return ::AsNum(deref(ref));
  }

  // Tracing functionality helps see recursive evals
  void StartEvalTrace(ExprRef ref) {
    for (int i = 0; i < trace_depth_; ++i) {
      Log(1) << " ";
    }
    Log(1) << std::setw(3) << trace_depth_ << " ";
    Log(1) << "EVAL " << ExprToString(ref) << std::endl;
    trace_depth_ += 1;
  }

  void EndEvalTrace(ExprRef ref) {
    trace_depth_ -= 1;
    for (int i = 0; i < trace_depth_; ++i) {
      Log(1) << " ";
    }
    Log(1) << std::setw(3) << trace_depth_ << " ";
    Log(1) << "---> " << ExprToString(ref) << std::endl;
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
      LoadFunc(line);
    }
  }

  // Dumps info about loaded functions.
  void Dump() {
    for (const auto func : funcs_) {
      std::cout << func.first << " = " << ExprToString(func.second) << std::endl;
    }
    std::cout << "galaxy" << " = " << ExprToString(funcs_[std::string("galaxy")]) << std::endl;
    std::cout << ":1338" << " = " << ExprToString(funcs_[std::string(":1338")]) << std::endl;
  }

  // Eval loop from pseudocode
  ExprRef Eval(ExprRef ref) {
    StartEvalTrace(ref);

    auto& expr = deref(ref);
    if (expr.evaluated != noexpr) {
      EndEvalTrace(expr.evaluated);
      return expr.evaluated;
    }

    ExprRef initial_ref = ref;
    ExprRef current_ref = ref;
    while (true) {
      ExprRef result = TryEval(current_ref);
      if (result == current_ref) {
        deref(initial_ref).evaluated = result;
        EndEvalTrace(result);
        return result;
      }
      current_ref = result;
    }
  }

  // TryEval from pseudocode
  ExprRef TryEval(ExprRef ref) {
    const auto& expr = deref(ref);
    if (expr.evaluated != noexpr) {
      Log() << "TryEval cached ref " << ref << std::endl;
      return expr.evaluated;
    }

    Log() << "TryEval func test " << expr.name << std::endl;
    if (IsAtom(expr) && funcs_.count(expr.name) != 0) {
      Log() << "TryEval ref is func " << ref << std::endl;
      return funcs_[expr.name];
    }

    if (IsAp(expr)) {
      Log() << "TryEval ref is Ap " << ref << std::endl;
      const auto x_ref = expr.arg;
      const auto func_ref = Eval(expr.func);

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
            return Atom(AsNum(Eval(y_ref)) / AsNum(Eval(x_ref)));
          }
          if (func2.name == "lt") {
            return AsNum(Eval(y_ref)) < AsNum(Eval(x_ref)) ? t_ : f_;
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
              return Ap(z_ref, Ap(y_ref, x_ref));
            }
            if (func3.name == "cons") {
              return Ap(Ap(x_ref, z_ref), y_ref);
            }
          }
        }
      }
    }

    Log() << "hmmm" << std::endl;
    return ref;
  }

  // Also from pseudocode
  ExprRef EvalCons(ExprRef a, ExprRef b) {
    const ExprRef res = Ap(Ap(cons_, Eval(a)), Eval(b));
    deref(res).evaluated = res;
    return res;
  }

  void FlattenList(ExprRef ref, std::vector<ExprRef>& flattened) {
    const Expr& first = deref(ref);
    if (!IsAp(first)) {
      panic("failed parsing list, doesnt start with Ap");
    }

    const auto& second = deref(first.func);
    if (!IsAp(second)) {
      panic("failed parsing list, second not an Ap");
    }

    const auto& cons = deref(second.func);
    if (cons.name != "cons") {
      panic("failed parsing list, no cons");
    }

    flattened.push_back(second.arg);
    
    const auto& next = deref(first.arg);
    if (next.name != "nil") {
      FlattenList(first.arg, flattened);
    }
  }

  std::vector<ExprRef> FlattenList(ExprRef ref) {
    std::vector<ExprRef> flattened;

    if (deref(ref).name != "nil") {
      FlattenList(ref, flattened);
    }
    return flattened;
  }

  Vec FlattenVec(ExprRef ref) {
    const Expr& first = deref(ref);
    if (!IsAp(first)) {
      panic("failed parsing vec, doesnt start with Ap");
    }

    const auto& second = deref(first.func);
    if (!IsAp(second)) {
      panic("failed parsing vec, second not an Ap");
    }

    const auto& cons = deref(second.func);
    if (cons.name != "cons") {
      panic("failed parsing vec, no cons");
    }

    Vec v;
    v.x = AsNum(second.arg);
    v.y = AsNum(first.arg);
    return v;
  }

  std::vector<Vec> FlattenVecList(ExprRef ref) {
    std::vector<Vec> vec_list;
    auto flattened = FlattenList(ref);
    for (const auto vec_ref : flattened) {
      vec_list.push_back(FlattenVec(vec_ref));
    }
    return vec_list;
  }

  void RenderPix(Vec v) {
    Vec offset = {v.x + kXOffset, v.y + kYOffset};
    for (int i = 0; i < kPixScale; ++i) {
      for (int j = 0; j < kPixScale; ++j) {
        SDL_RenderDrawPoint(renderer_, offset.x*kPixScale + i, offset.y*kPixScale + j);
      }
    }
  }

  void RenderVecList(const std::vector<Vec>& vlist) {
    for (const auto& v: vlist) {
      RenderPix(v);
    }
  }
  
  // Fake for now
  ExprRef SEND_TO_ALIEN_PROXY(ExprRef ref) {
    panic("send");
    return ref;
  }

  struct InteractResult {
    ExprRef data;
    ExprRef pics;
  };
  
  // Returns a new data blob and a list of "pictures".
  InteractResult InteractGalaxy(ExprRef state, ExprRef event) {
    ExprRef eref = Ap(Ap(Atom("galaxy"), state), event);
    ExprRef res = Eval(eref);

    // GET_LIST_ITEMS_FROM_EXPR(...)
    auto flat = FlattenList(res);
    if (flat.size() != 3) {
      panic("response from galaxy not a triple");
    }

    const ExprRef flag = flat[0];
    const ExprRef new_state = flat[1];
    const ExprRef data = flat[2];

    std::cout << "GALAXY BRAIN : " << ExprToString(flag) << " | "
              << ExprToString(new_state) << " | "
              << ExprToString(data) << std::endl;
    if (AsNum(flag) == 0) {
      InteractResult result;
      result.data = new_state;
      result.pics = data;
      return result;
    }

    return InteractGalaxy(new_state, SEND_TO_ALIEN_PROXY(data));
  }

	bool PollForClick(Vec* v) {
    std::cout << "waiting for click" << std::endl;
		SDL_Event e;
    while (true) {
      while(SDL_PollEvent(&e)){
        switch(e.type){
          case SDL_QUIT:
            return true;
        case SDL_MOUSEBUTTONDOWN:
          if (e.button.button == SDL_BUTTON_LEFT) {
            std::cout << "CLEEK " << e.button.x << " " << e.button.y << std::endl;
            v->x = e.button.x/kPixScale - kXOffset;
            v->y = e.button.y/kPixScale - kYOffset;
            return false;
          }
          break;
        }
      }
    }
	}

  void PRINT_IMAGES(ExprRef imgs) {
    auto img_list = FlattenList(imgs);

    SDL_SetRenderDrawColor(renderer_, 0, 0, 0, 255);
    SDL_RenderClear(renderer_);

    for (int i = 0; i < img_list.size(); ++i) {
      const int idx = img_list.size() - 1 - i;
      auto vlist = FlattenVecList(img_list[idx]);
      SDL_SetRenderDrawColor(renderer_, 50*(i+1), 50*(i+1), 50*(i+1), 255);
      RenderVecList(vlist);
    }
		SDL_RenderPresent(renderer_);
  }

  void MainLoop() {
    ExprRef state = nil_;
		Vec click_vec = {0, 0};

		while(true) {
			ExprRef click = Ap(Ap(cons_, Atom(click_vec.x)), Atom(click_vec.y));
      auto ires = InteractGalaxy(state, click);
      PRINT_IMAGES(ires.pics);

      const bool should_quit = PollForClick(&click_vec);
      if (should_quit) {
        return;
      }

      state = ires.data;
		}
  }

  // Runs the first step of the galaxy protocol, just for debugging, will go
  // away soon...
  ExprRef TestOneStep() {
    auto state = nil_;
    ExprRef click = Ap(Ap(cons_, Atom(0)), Atom(0));

    ExprRef eref = Ap(Ap(Atom("galaxy"), state), click);
    ExprRef res = Eval(eref);

    return res;
  }

  size_t num_exprs() const { return exprs_.size(); }

 private:
  ExprRef cons_;
  ExprRef t_;
  ExprRef f_;
  ExprRef nil_;

  int trace_depth_ = 0;

  // The Expr pool. Currently we don't recycle Exprs, they grow in an unbounded
  // fashion until we run out of memory. We can fix this if needed.
  std::vector<Expr> exprs_;

  // Map of function names to bodies that we use to substitute for the function
  // names during Eval.
  std::unordered_map<std::string, ExprRef> funcs_;

	// SDL state used for shit
	SDL_Renderer* renderer_;
};

// Simple main test...
int main(int argc, char** argv) {
  if (argc != 2 && argc != 3) {
    std::cerr << "usage: interp <galaxy.txt path>" << std::endl;
    std::cerr << "usage (repl): interp repl <optional funcs.txt path>" << std::endl;
    return -1;
  }

  if (std::string(argv[1]) == "repl") {
    std::cout << "Welcome to REPL mode!" << std::endl;

    Engine engine(1000, nullptr);
    if (argc == 3) {
      std::cout << "Loading additional funcs from " << argv[2] << "..." << std::endl;
      engine.LoadFuncs(argv[2]);
    }

    while (true) {
      std::string line;
      std::cout << "> ";
      std::getline(std::cin, line);

      std::cout << std::endl;
      auto split_line = split(line, " ");
      const auto result = engine.Deserialize(0, split_line);
      if (result.pos != split_line.size()) {
        std::cout << "Bad input" << std::endl;
      }
      std::cout << engine.ExprToString(engine.Eval(result.expr));
      std::cout << std::endl;
    }
  }

	SDL_Event event;
	SDL_Renderer *renderer;
	SDL_Window *window;
	int i;

	SDL_Init(SDL_INIT_VIDEO);
	SDL_CreateWindowAndRenderer(WINDOW_WIDTH, WINDOW_WIDTH, 0, &window, &renderer);

  Engine engine(1000, renderer);
  engine.LoadFuncs(argv[1]);
  engine.MainLoop();
  //engine.Dump();

  // TEST AYY LMAO
  auto res = engine.TestOneStep();
  std::cout << "RESULT: " << std::endl << engine.ExprToString(res) << std::endl;
  std::cout << "NUM EXPRS: " << std::endl << engine.num_exprs() << std::endl;
	SDL_DestroyRenderer(renderer);
	SDL_DestroyWindow(window);
	SDL_Quit();
  return 0;
}
