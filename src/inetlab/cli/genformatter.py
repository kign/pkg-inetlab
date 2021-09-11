import os, sys
import re


class GenericFormatter :
    def __init__ (self, format_str) :
        opts = format_str.split(',')
        pars = {}
        for x in opts[1:] :
            k,v = x.split('=')
            pars[k] = v
        if opts[0] == "aligned" :
            self._formatter = AlignedFormatter(pars)
        elif opts[0] == "csv" :
            self._formatter = CSVFormatter(pars)
        else :
            raise Exception("Invalid formatter " + opts[0])

    def writerow(self,row) :
        return self._formatter.writerow(row)

    def writeheader(self,row) :
        try :
            return self._formatter.writeheader(row)
        except AttributeError :
            return self._formatter.writerow(row)

    def close(self) :
        return self._formatter.close()


class CSVFormatter :
    def __init__ (self,pars) :
        import csv
        self.out = csv.writer(sys.stdout)
    def writerow(self,row) :
        self.out.writerow(row)
    def close(self) :
        pass


class AlignedFormatter :
    def __init__ (self, pars) :
        self.rows = []
        self.alignchar = '|'
        self.alignchar1 = '+'
        self.width = None if 'width' not in pars else int(pars.get('width'))
        self.header = 1
        self.cont = "~"
        self.fill_last = False
        if pars.get('fill_last','n').lower() in ['yes','y','true','t'] :
            _, self.term_width = os.popen('stty size', 'r').read().split()
            self.term_width = int(self.term_width)
            self.fill_last = True
        
    def writerow(self, row) :
        if self.rows :
            assert len(self.rows[0]) == len(row)
        self.rows.append(row)
        
    def close(self) :
        def getcol(row,irow) :
            x = row[irow]
            if type(x) == tuple :
                x = x[1]
            if not isinstance(x, str) :
                x = str(x)
            return x
        def getcolfmt(row,irow) :
            x = row[irow]
            fmt = None
            if type(x) == tuple :
                x = x[1]
                fmt = x[0]
            if not isinstance(x, str) :
                x = str(x)
            if fmt is not None :
                x = fmt(x)
            return x
        def getfmt(row,irow) :
            x = row[irow]
            if type(x) == tuple :
                return x[0]
            else :
                return lambda y : y

        def ulen(s) :
            s = re.compile(r'\x1b.+?m').sub('', s)
            try :
                from wcwidth import wcswidth
                return wcswidth(s)
            except ModuleNotFoundError :
                return len(s)

        if not self.rows :
            return
        colw = []
        for idx in range(len(self.rows[0])) :
            colw.append(max(ulen(getcol(row,idx)) for row in self.rows))
        if self.width is not None :
            for idx in range(len(colw)) :
                if idx > 0 and colw[idx] > self.width :
                    colw[idx] = self.width

        if self.fill_last :
            colw[-1] = self.term_width - 1 - 3*(len(colw)-1) - sum(colw[:-1])
        i_row = 0
        for row in self.rows :
            i_row += 1
            res = []
            for idx in range(len(row)) :
                s = getcol(row,idx)
                f = getfmt(row,idx)
                if ulen(s) <= colw[idx] :
                    s = s + " " * (colw[idx] - ulen(s))
                else :
                    # FIXME: this must be re-written for wide unicode chars
                    s = s[:colw[idx] - len(self.cont)] + self.cont
                res.append(f(s))
            print((' ' + self.alignchar + ' ').join(res))
            if self.header is not None and self.header == i_row :
                res = []
                for idx in range(len(row)) :
                    res.append("-" * ((1 if idx == 0 else 2)+colw[idx]))
                print(self.alignchar1.join(res))
