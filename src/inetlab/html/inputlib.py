from ..utils.mylangutils import *
from .htmlbuilder import *

def InputString (indent, name, prompt=None, init="", **attrs) :
    if not prompt : prompt = ""
    return IF ( prompt, prompt + "\n", "" ) + \
           INPUT ( indent, "text", name, value=init, **attrs )

# Make sure parent form has looks like that:
# FORM ( 1, 'upload', 'post', $url, 'enctype', "multipart/form-data", ...
def InputFile (indent, name, prompt=None, **attrs) :
    return IF ( prompt, prompt + "\n", "" ) + \
           INPUT ( indent, "file", name, **attrs )

def InputEnum (indent, name, prompt, init, **attrs) :
    if prompt is None : prompt = ""
    elems = []
    for opt in init :
        ats = { 'value' : opt }
        if opt == init.val :
            ats['selected'] = True
        if type(prompt) != type("") and type(prompt) != type("") and opt in prompt :
            ats['_'] = prompt[opt]
        elif type(opt) == type("") or type(opt) == type("") :
            ats['_'] = htmlspecialchars (opt)
        else :
            ats['_'] = htmlspecialchars (str(opt))
        elems.append ( TAG ( "OPTION", indent + 1, **ats ) )
    pr = ""
    if prompt and type(prompt) == type("") :
        pr = prompt + "\n"
    return pr + TAG ( "SELECT", indent, name = name, _="\n".join ( elems ), **attrs )

def InputEnumRadio (indent, name, prompt, init, optprefix="", optsuffix="\n",
                    escapeHTML=True, disabled=[], **attrs) :
    import copy
    elems = []
    for opt in init :
        ats = copy.copy(attrs)
        if opt == init.val :
            ats['checked'] = True
        pr = opt
        if type(prompt) == type({}) and opt in prompt :
            pr = prompt[opt]
    if not escapeHTML and pr.lower().find('<input') >= 0 :
        tag_pr = pr
    else :
        tag_pr =  TAG ( "LABEL", indent, _=IF ( escapeHTML, htmlspecialchars(pr), pr ),
                **{'for':name + "_" + opt} )
        elems += [optprefix +
                  INPUT ( indent, 'radio', name, id=name + "_" + opt,
              disabled=(opt in disabled),
                          value=opt, **ats ) +
                  tag_pr +
                  optsuffix]
    return "".join ( elems )

def InputBool ( indent, name, prompt, init, placement="right", **attrs ) :
    from random import randint
    id = attrs.get('id',name + str(randint(1000,9999)))
    if 'id' in attrs: del attrs['id']
    if init:
        attrs['checked'] = True
    tag = INPUT ( indent, 'checkbox', name, value='on', id=id, **attrs )
    if not prompt :
        return tag
    label = TAG ( "LABEL", indent, _=prompt, **{'for': id} )
    if placement == "right" :
        return tag + label
    elif placement == "left" :
        return label + tag
    else :
        raise Exception ( "InputBool: invalid value prompt='" + str(prompt) + "'" )

def InputText ( indent, name, prompt, rows, init, **attrs ) :
    cols = attrs.pop('cols',80)
    return DIV ( indent,
                 DIV ( indent + 1, align='center', _=prompt ) + "\n" +
                 TEXTAREA ( 0, name, cols=cols, rows=rows, **attrs ) +
                 htmlspecialchars (init) + "</textarea>" )

def InputEnum2 (indent, name, name2, prompt, init, submenus, **shared_attrs) :
    # 'submenus' maps *some* values from 'init' to
    #                pair (subprompt, subinit)
    #                 ... where subprompt, subinit could be any legal entry to InputEnum

    # re-writing attributes dict to turn all keys into lower-case
    if shared_attrs :
        t_attrs = {}
        for k, v in shared_attrs.items () :
            if k.lower() in t_attrs :
                raise "Duplicate key %s (differenrt capitalization)" % k
            t_attrs[k.lower()] = v
        shared_attrs = t_attrs

#    onchange_func = shared_attrs.pop('onchange', None)

    mainattrs = shared_attrs.copy ()

    onchange_func = mainattrs.pop('onchange', None)

    sublist = [x for x in init if x in submenus]

    mainattrs['onChange'] = " ".join ( [
            "document.getElementById('%s_%s').style.visibility = (this.options[this.selectedIndex].value == '%s')?'visible':'hidden';" % (name2,val,val)
            for val in sublist] )
    if onchange_func :
        mainattrs['onChange'] = "if (%s) { %s }" % (onchange_func, mainattrs['onChange'])

    ui_menu = InputEnum (indent, name, prompt, init, ** mainattrs)
    ui_submenu = ""

    for val in sublist :
        vis = "hidden"
        if val == init.val : vis = "visible"
        subattrs = shared_attrs.copy ()
        assert 'id' not in subattrs
        subattrs['id'] = name2 + "_" + val
        if 'style' not in subattrs: subattrs['style'] = ""
        subattrs['style'] += " visibility: %s; position: absolute; top: 0px; right: 0px;" % vis
        ui_submenu += InputEnum(indent, name2 + "_" + val, submenus[val][0], submenus[val][1], ** subattrs)

    return ui_menu, ui_submenu # DIV (1,style="position: relative; ", _=  "pre " + ui_submenu + " post")
