import json
from datetime import date as Date, timedelta, datetime
from dateutil.parser import parse as date_parse

class XMLObject(object) :
    
    def save_properties_as_attributes(self, xml_elm, *props) :
        for key in props :
            val = getattr(self,key)
            if val is not None and val != "":
                xml_elm.set(key,XMLObject.serialize(val))

    
    def populate_properties_from_attributes(self, xml_elm, *props) :
        args = {}
        t = None
        for p in props :
            if type(p) is type :
                t = p
            else :
                args[p] = XMLObject.deserialize(xml_elm.get(p),t)
        self.populate(** args)

    
    def save_properties_as_subnodes(self, xml_elm, *props) :
        from xml.etree.ElementTree import Element, SubElement
        for key in props :
            val = getattr(self,key)
            if val :
                if type(val) == list :
                    s = SubElement(xml_elm, key, type='array')
                    for ev in val :
                        et_ev = SubElement(s, "element")
                        et_ev.text = XMLObject.serialize(ev)
                else :
                    s = SubElement(xml_elm, key, type='text')
                    s.text = val

    
    def populate_properties_from_subnodes(self, xml_elm, *props) :
        for p in props :
            e = xml_elm.find("./" + p)
            if e is not None :
                etype = e.attrib.get('type','text')
                if etype == 'text' :
                    value = e.text
                elif etype == 'array' :
                    value = [XMLObject.deserialize(aelm.text,None) for aelm in xml_elm.findall("./" + p + "/element")]
                else :
                    raise RuntimeError('Subnode type {} not yet supported'.etype)
                self.populate(**{p : value})

    def populate(self, ** attrs) :
        for k, v in attrs.items () :
            setattr(self, k, v)

    @staticmethod
    def serialize_low(obj) :
        if isinstance(obj,datetime) :
            return obj.replace(microsecond=0).isoformat()
        if isinstance(obj,Date) :
            return obj.strftime("%m/%d/%Y")
        return None

    @staticmethod
    def serialize(obj) :
        return XMLObject.serialize_low(obj) or str(obj)

    @staticmethod
    def deserialize(s,type) :
        if s is None :
            return None
        if type is int :
            return int(s)
        if type is bool :
            return s.lower() in ['true', 't', '1', 'yes', 'y']
        if type is Date :
            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%Y-%m", "%Y"] :
                try :
                    return datetime.strptime(s,fmt).date()
                except ValueError :
                    pass
            raise ValueError("Cannot parse date %s" % s)
        if type is datetime :
            return date_parse(s)
        return s
