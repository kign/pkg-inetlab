from .htmlbuilder import *

def BUTTON ( indent, name, value, env, **pars ):
    style = False
    if 'style' in pars : style = pars.pop('style')
    
    return INPUT ( indent, "button", name, id=name, style=style,
                   value=value, onClick="window.location.href='%s'" %
                   env.modurl ( ** pars ) )

def BUTTON1 ( indent, name, value, url, **attrs ):
    return INPUT ( indent, "button", name, id=name,
                   value=value, onClick="window.location.href='%s'" % url,
                   **attrs )

def TABUI (tablist, tabprops, curtab, props) :
    if props is None : props = {}

    content_dir = props.get('content_dir', "ltr")

    tabs = []
    ctab = None
    for ii in range(len(tablist)) :
        tt = tablist[ii]
        props = tabprops.get(tt,{})
        name = props.get('name',tt)
        url = None
        if tt == curtab :
            ctab = ii
        else :
            url = props.get('url',None)
        if url :
            tab = A(0,url,name)
        else :
            tab = name
        tabs.append(tab)

    assert ctab is not None, \
        "curtab = %r isn't in the list %r" % (curtab, tablist)
    
#    tabs = ["tab 1", "tab 2", "tab 3", "tab 4"]
#    ctab = 1
    
    border = 'solid rgb(200,200,200) 1px'
    bg = 'inherit'

    headers = []
    left = "left"
    right = "right"
    if content_dir == "rtl" :
        left = "right"
        right = "left"
    for ic in range(len(tabs)) :
        draw =                               ['top',left]
        if ic == len(tabs) - 1 : draw += [right]
        if ic != ctab : draw += ['bottom']
        styles = ["border-%s: %s" % (x,border) for x in draw]
        if ic == ctab : styles += ['background-color: ' + bg]

        headers.append (TD ( 6, NOWRAP=True, style="white-space: nowrap; width: 1px; " + "; ".join(styles), _= tabs[ic] ))

    headers.append(TD ( 6, style='width: auto; border-bottom: ' + border, _="&nbsp;" ))

    return \
        TABLE ( 1, border=0,  cellspacing=0, cellpadding=5, style="margin-top: 3px;",  _=
                TR ( 2, _= "\n".join(headers)))

