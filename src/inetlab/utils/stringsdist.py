def strings_distance(_s1,_s2) :
    s1 = _s1.lower ()
    s2 = _s2.lower ()
    n1 = len(s1)
    n2 = len(s2)

    d = 0
    for ii in range(min(0, n1-n2) - 1, 1 + max(0, n1-n2)) :
        s = 0
        jj = max(0, ii)
        while jj < min(n1,n2+ii) :
            kk = 0
            while jj + kk < min(n1,n2+ii) and s1[jj:1 + jj + kk] == s2[jj - ii:1+ jj - ii + kk] :
                kk += 1
            if kk >= 2 :
                s += kk
            jj += kk + 1
        if s > 1 :
            d += s**1.5

    return d/(n1*n2)**(1.5/2)

def _strings_distance(_s1,_s2) :
    s1 = _s1.lower ()
    s2 = _s2.lower ()
    n1 = len(s1)
    n2 = len(s2)

    desc = []
    d = 0
    for ii in range(min(0, n1-n2) - 1, 1 + max(0, n1-n2)) :
        s = 0
        jj = max(0, ii)
        while jj < min(n1,n2+ii) :
            kk = 0
            while jj + kk < min(n1,n2+ii) and s1[jj:1 + jj + kk] == s2[jj - ii:1+ jj - ii + kk] :
                kk += 1
            if kk >= 2 :
                s += kk
            jj += kk + 1
        if s > 1 :
            desc.append(f"{ii}|{s}")
            d += s**1.5

    return d/(n1*n2)**(1.5/2), " ".join(desc)

def strings_distance_test(_s1,_s2) :
    return _strings_distance(_s1, _s2)

if __name__ == '__main__':
    import random, string
    from genformatter import GenericFormatter

    random.seed(13)
    lets = string.ascii_lowercase + string.ascii_uppercase
    x1 = ''.join(random.choice(lets) for i in range(18))
    x2 = ''.join(random.choice(lets) for i in range(20))
    x3 = ''.join(random.choice(lets) for i in range(20))


    TESTS = [('Vasya', 'Vasya'),
             ('Alexander', 'Aleksansr'),
             ('abrokd', 'sertja'), ('sertja', 'abrokd'),
             (x1, x2), (x2, x1), (x3, x3),
             ('Peter vorinon', 'pete varonin'),
             ('IDC var', 'my IDC'),
             ('Kathina Bergant', 'Sublet of Kathina Bergant'),
             ('City of Cambridge', 'City Clerk, City of Cambridge'),
             ('Valender Realty', 'Valender Real Estate'),
             ('Yifi Yang', 'Yimi Yao'),
             ('Eversource', 'Eversource Electric'),
             ('ALD Insurance', 'Amity Insurance'),
             ('Seckel Condo Association', 'Kirkland Street Condo Association'),
             ('Amity Insurance', 'MAPFRE Insurance'),
             ("John's Sewer", "John's"),
             ('ALD Insurance', 'Rodman Insurance'),
             ('ALD Insurance', 'MAPFRE Insurance'),
             ('my properties', 'his properties'),
             ('WCB', 'WHB'),
             ('ALD Insurance', 'Commerce Insurance'),
             ('Aleksei Pakherev', 'Alexey Pakherev'),
             ('Northern Security Insurance Company', 'Susan Curran'),
             ('Ketian Zhang', 'American Heating and Cooling'),
             ('Alia Obiad', 'Elia'),
             ('Eliani Oliveira', 'Igor Oliveira')]

    out = GenericFormatter("aligned,width=80")
    print()
    out.writeheader(['First', 'Second', 'Dist', 'Desc'])
    for p1,p2 in TESTS :
        dist, desc = strings_distance_test(p1, p2)
        out.writerow([p1, p2, dist, desc])

    out.close()

