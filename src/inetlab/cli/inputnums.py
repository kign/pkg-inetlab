import re, logging

def input_numbers(prompt, n, flat: bool, extend=None) :
    """User can input any number or ranges between 1 and n, e.g.: 1,5,8-11

    It is also possible to use "except ..." syntax, e.g. "except 10, 15"

    Parameters:

        - flat (bool, default=False)   return flat list of numbers, not list of intervals

        - extend(array of strings, default=[])  provide additional list of valid entries, in addition to
            o numbers and intervalis
            o 'quit', 'all' or 'none' (case insensitive and could be shortened to 1-st letter)
    """
    p = None
    while True :
        try :
            resp = input(prompt).strip('\t, ').lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return None

        if extend and resp in extend :
            return resp

        elif resp in ['q', 'quit'] :
            return None

        elif resp in ['a', 'all'] :
            p = [(1,n)]
            break

        elif resp in ['n', 'none'] :
            p = []
            break

        elif resp == '' :
            continue

        resp, invert = _invert_prefix(resp)

        try :
            p = _split_ints(resp, n)
        except RuntimeError as err :
            logging.error(str(err))
            continue

        itr = _normalize_ints(p)
        if invert :
            _invert_ints(p, n)

        if itr > 0 or invert :
            x = input(f"This is what you want: {_print_ints(p)}; correct [yes]? ").strip().lower()
            if x in ['', 'y', 'yes'] :
                break
            print("Let's try again...")
            continue
        else :
            break

    if not flat :
        return p

    pf = []
    for a,b in p :
        pf.extend(range(a,b+1))

    return pf


def _invert_prefix(inp) :
    invert = False
    if inp.startswith('except ') :
        inp = inp[7:]
        invert = True

    return inp, invert


def _invert_ints(p, n) :
    lp = len(p)
    if lp == 0 :
        p.append((1,n))
        return
    if p[0][0] > 1 :
        p.append((1,p[0][0]-1))
    for ii in range(lp-1) :
        p.append((p[ii][1]+1, p[1+ii][0]-1))
    if p[lp-1][1] < n :
        p.append((p[lp-1][1]+1, n))

    del p[:lp]


def _split_ints(inp, n) :
    def one_elm(s) :
        m = re.compile(r'\s*(\d+)\s*(?:-\s*(\d+))?\s*$').match(s)
        if not m:
            raise RuntimeError(f"Cannot parse {s}")
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) is not None else a
        if a == 0 or a > n :
            raise RuntimeError(f"Start of interval {s} invalid, must be between 1 and {n}")
        if b == 0 or b > n :
            raise RuntimeError(f"End of interval {s} invalid, must be between 1 and {n}")
        if b < a :
            raise RuntimeError(f"Invalid interval {a}-{b}")
        return a, b

    return sorted(map(one_elm, re.compile(r'[, ]+').split(inp)), key=lambda x:x[0])


def _normalize_ints(p) :
    changing = True
    itr = 0
    while changing and itr < 100:
        changing = False
        np = len(p)
        ii = 0
        while ii < np - 1 :
            assert p[ii][0] <= p[ii+1][0]
            if p[ii+1][0] <= 1 + p[ii][1] :
                p.append((p[ii][0], max(p[ii][1], p[ii+1][1])))
                del p[ii:ii+2]
                np -= 2
                changing = True
            else :
                ii += 1
        if changing :
            itr += 1
            p.sort(key=lambda x:x[0])

    return itr


def _print_ints(p) :
    return ','.join(str(a) if a == b else (f'{a},{b}' if b == a + 1 else f'{a}-{b}') for a,b in p)


if __name__ == "__main__" :
    import os, sys

    try :
        mode = sys.argv[1]
    except IndexError :
        print(f"Usage: {sys.argv[0]} <auto|manual>")
        exit(0)

    if mode == "auto" :
        from genformatter import GenericFormatter

        TESTS = [
            ("2-1", False),
            ("1,2,3,4,5,6,7", "1-7"),
            ("except 1-5", "6-10", 10),
            ("except 2-3,3-5,11", "1,6-10", 11),
            ("except 1,3-5,6-9", "2,10", 10),
            ("1-4 2-5 3-6 12 10,    8", "1-6,8,10,12"),
            ("10,26,27 8, 11 20 12","8,10-12,20,26,27")]

        failed = []
        for test in TESTS :
            try :
                inp, exp, n = test
            except ValueError:
                inp, exp, n = test + (100,)
            try :
                inp1, invert = _invert_prefix(inp)
                p = _split_ints(inp1, n)
                _normalize_ints(p)
                if invert :
                    _invert_ints(p,n)
                res = _print_ints(p)
            except RuntimeError as err:
                # print_exception(*sys.exc_info())
                res = False

            if res != exp :
                failed.append((inp,exp,res))

        if failed :
            print(f"Passed {len(TESTS) - len(failed)}/{len(TESTS)}")

            print("Failed tests:\n")
            out = GenericFormatter("aligned,width=80")
            out.writeheader(['Input', 'Expected', 'Actual'])
            for inp, exp, res in failed :
                out.writerow([inp, "FAIL" if exp is False else exp, "FAIL" if res is False else res])
            out.close ()

        else :
            print(f"Passed all {len(TESTS)} tests")

    elif mode == "manual" :
        n = 25
        res = input_numbers("Enter desired number(s) or interval(s), Quit, All, or None > ", n, flat=True)
        print("input_numbers returned", res)
    else :
        print("Unknown test mode =", mode)





