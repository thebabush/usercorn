import cffi


CDEF = r'''
extern "Python" void print_func(int);

// Defined in Go
typedef unsigned int paddr;

extern void PDec(paddr addr);
extern char* _usercorn_getExe(paddr addr);
extern void _usercorn_setHookSysAdd(void (*)(int));

// Other stuff
void free(void *);
'''

SOURCE = r'''
typedef void (*callback_fcn)(int);

void call_callback_fcn(callback_fcn cb, int val) {
    cb(val);
}
'''

EMBEDDING_API = r'''
typedef unsigned int paddr;

// Defined in Python
void call_python(paddr addr);
void on_init(paddr uc);
'''

INIT_CODE = r'''
from __future__ import print_function

from usercorn import _ffi, _lib


class Autofree(object):
    def __new__(cls, cp, *args, **kwargs):
        cp_ = cp
        if '_af_convert' in cls.__dict__:
            cp = cls._af_convert(cls, cp)
        self = super(Autofree, cls).__new__(cls, cp)
        self._pointer = cp_
        return self

    def __del__(self):
        _lib.free(self._pointer)
        p = super(Autofree, self)
        if '__del__' in p.__class__.__dict__:
            super(Autofree, self).__del__()


class String(Autofree, str):
    @staticmethod
    def _af_convert(cls, cp):
        return _ffi.string(cp)


@_ffi.def_extern()
def call_python(addr):
    print('call_python({})'.format(addr))


@_ffi.def_extern()
def print_func(arg):
    print("callback({})".format(arg))


@_ffi.def_extern()
def on_init(uc):
    exe = String(_lib._usercorn_getExe(uc))
    print("EXE:", exe)
    _lib._usercorn_setHookSysAdd(_lib.print_func)
    uc = Usercorn(uc)


class Usercorn(object):
    def __init__(self, native):
        self._native = native

    def __del__(self):
        _lib.PDec(self._native)
'''


def build_cffi():
    ffi = cffi.FFI()
    ffi.cdef(CDEF)
    ffi.set_source('_usercorn', SOURCE)
    ffi.embedding_api(EMBEDDING_API);
    ffi.embedding_init_code(INIT_CODE)
    return ffi


if __name__ == '__main__':
    ffi = build_cffi()
    ffi.emit_c_code('./python_binding.c')

