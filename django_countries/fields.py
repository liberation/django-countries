from django.db.models.fields import CharField
from django.utils.encoding import force_unicode
from django_countries import settings


class Country(object):
    def __init__(self, code):
        self.code = code
    
    def __unicode__(self):
        return force_unicode(self.code or u'')

    def __eq__(self, other):
        return self.code == force_unicode(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        return cmp(self.code, force_unicode(other))

    def __hash__(self):
        return hash(self.code)

    def __repr__(self):
        return "%s(code=%r)" % (self.__class__.__name__, self.code)

    def __nonzero__(self):
        return bool(self.code)

    def __len__(self):
        return self.code.size
    
    @property
    def name(self):
        # Local import so the countries aren't loaded unless they are needed. 
        from django_countries.countries import COUNTRIES
        for code, name in COUNTRIES:
            if self.code == code:
                return name
        return ''
    
    @property
    def flag(self):
        if not self.code:
            return ''
        return settings.FLAG_URL % {'code_upper': self.code,
                                    'code': self.code.lower()}


class CountryDescriptor(object):
    """
    A descriptor for country fields on a model instance. Returns a Country when
    accessed so you can do stuff like::

        >>> instance.country.name
        u'New Zealand'
        
        >>> instance.country.flag
        '/static/flags/nz.gif'
    """
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))
        return Country(code=instance.__dict__[self.field.name])

    def __set__(self, instance, value):
        # Don't understand now why this force_unicode
        # It creates some trouble with NoneType
        # I'll think about this later
        if value == None:
            value = ''
        instance.__dict__[self.field.name] = force_unicode(value)


class CountryField(CharField):
    """
    A country field for Django models that provides all ISO 3166-1 countries as
    choices.
    
    """
    descriptor_class = CountryDescriptor
 
    def __init__(self, *args, **kwargs):
        # Local import so the countries aren't loaded unless they are needed. 
        from django_countries.countries import COUNTRIES 

        kwargs.setdefault('max_length', 2) 
        kwargs.setdefault('choices', COUNTRIES) 

        super(CharField, self).__init__(*args, **kwargs) 

    def get_internal_type(self): 
        return "CharField"

    def contribute_to_class(self, cls, name):
        super(CountryField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))

    def get_prep_lookup(self, lookup_type, value):
        if hasattr(value, 'code'):
            value = value.code
        return super(CountryField, self).get_prep_lookup(lookup_type, value)

    def pre_save(self, *args, **kwargs):
        "Returns field's value just before saving."
        value = super(CharField, self).pre_save(*args, **kwargs)
        return self.get_prep_value(value)

    def get_prep_value(self, value):
        "Returns field's value prepared for saving into a database."
        # Convert the Country to unicode for database insertion.
        if value is None:
            return None
        return unicode(value)


# If south is installed, ensure that CountryField will be introspected just
# like a normal CharField.
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^django_countries\.fields\.CountryField'])
except ImportError:
    pass
