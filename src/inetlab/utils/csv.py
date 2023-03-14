import re, io, keyword, csv, logging
from collections import namedtuple

def read_csv(fname, skip_rows=0, skip_cols=0, skip_empty=True) :
    # Have to untangle buffered text reading in Python to remove possible BOM header
    # (PayPay CSV export adds BOM to UTF-8 files, WTF?)
    empty = 0
    with io.FileIO(fname) as fh_raw :
        with io.BufferedReader(fh_raw) as fh_bytes :
            if fh_bytes.peek(3)[:3] == b'\xef\xbb\xbf' :
                fh_bytes.read(3)
            with io.TextIOWrapper(fh_bytes, encoding='UTF-8') as fh_text :
                r = csv.reader(fh_text)
                for _ in range(skip_rows) :
                    next(r)
                headers = [normalize_csv_header(h) for h in next(r)[skip_cols:]]
                logging.debug("reading %s, headers = %r", fname, headers)
                csvacnt = namedtuple('csvacnt', headers)

                res = []
                for idx,row in enumerate(r) :
                    if skip_empty and all(x == '' for x in row[skip_cols:]) :
                        empty += 1
                        continue
                    try :
                        obj = csvacnt._make(row[skip_cols:])
                        res.append(obj)
                    except TypeError as e :
                        # Excel row count begins from 1, from
                        logging.error("Row %d returned exception %s", idx + skip_rows + 2, e)
                if empty > 0 :
                    logging.warning("Skipping %d empty rows", empty)
                return res

nch_cnt=0
def normalize_csv_header(h) :
    global nch_cnt
    if h == "" :
        nch_cnt += 1
        h = "undef_%d" % nch_cnt
    else :
        h = re.sub(r'_+$', '', re.sub(r'_+', '_', h.lower().replace(' #','').replace(" ","_").replace('#','').replace('(','').replace(')','').replace('@','_at_').replace('-','_').replace('$','_')))
        if h in keyword.kwlist :
            h = h + "_"
        if h == "propery" :
            h = "property"
    return h
