package python

/*
#cgo pkg-config: python2
#cgo LDFLAGS: -L../../ -lpython_binding

#include <stdlib.h>

typedef unsigned int paddr;

void call_python(paddr addr);
void on_init(paddr cpu);

// Callback test
typedef void (*callback_fcn)(int);
void call_callback_fcn(callback_fcn cb, int arg);
*/
import "C"

import (
  "fmt"

  "github.com/lunixbochs/usercorn/go/models"
)

type PAddr = C.uint;
type PValue = interface{};

type PRef struct {
  counter uint
  value   *PValue
}

var ptrs = map[PAddr]PRef{};
var nextAddr PAddr = 0;

func GetOpaque(addr PAddr) *PValue {
  if val, ok := ptrs[addr]; ok {
    return val.value
  }
  panic(fmt.Sprintf("Invalid opaque address: %v", addr))
}

func MkOpaque(value PValue) PAddr {
  addr := nextAddr
  if _, exists := ptrs[addr]; exists {
    panic(fmt.Sprintf("Value is already opaque: %v", value));
  }
  ptrs[addr] = PRef{1, &value}
  nextAddr++;
  return addr;
}

//export PDec
func PDec(addr PAddr) {
  if val, exists := ptrs[addr]; exists {
    if val.counter > 0 {
      val.counter--
    }
    if val.counter == 0 {
      delete(ptrs, addr)
    }
  } else {
    panic(fmt.Sprintf("PDec received a non-existing address: %d", addr))
  }
}

//export PInc
func PInc(addr PAddr) {
  if val, exists := ptrs[addr]; exists {
    val.counter++
  } else {
    panic(fmt.Sprintf("PInc received a non-existing address: %d", addr))
  }
}

//export _usercorn_getExe
func _usercorn_getExe(addr PAddr) *C.char {
  v := (*GetOpaque(addr)).(models.Usercorn)
  return C.CString(v.Exe())
}


//export _usercorn_setHookSysAdd
func _usercorn_setHookSysAdd(fn C.callback_fcn) {
  C.call_callback_fcn(fn, 666)
}


func ExecScript(usercorn models.Usercorn, cmd string) int {
  opaque := MkOpaque(usercorn)
  C.on_init(opaque)
  C.call_python(0)
  fmt.Println("===============================================\n\n")
  return 0
}

