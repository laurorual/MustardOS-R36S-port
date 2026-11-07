#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Original NROM-128 cartridge: yellow ship, blue sky, D-pad; silent APU.
No Nintendo code, font, music, BIOS or artwork. A tiny fixed 6502 emitter keeps
build dependencies inside Python; actual emulation/API tests validate behavior.
"""
from pathlib import Path
import argparse,json,hashlib
class Asm:
    def __init__(self):self.code=bytearray();self.labels={};self.fixups=[]
    def emit(self,*data):self.code.extend(data)
    def label(self,name):assert name not in self.labels;self.labels[name]=0x8000+len(self.code)
    def ref(self,opcode,label,relative=False):
        self.emit(opcode);self.fixups.append((len(self.code),label,relative));self.emit(0) if relative else self.emit(0,0)
    def finish(self):
        for at,label,relative in self.fixups:
            value=self.labels[label]
            if relative:
                delta=value-(0x8000+at+1);assert -128<=delta<=127;(self.code.__setitem__(at,delta&255))
            else:self.code[at:at+2]=value.to_bytes(2,'little')
        return self.code

def cartridge():
    a=Asm();a.label('reset');a.emit(0x78,0xD8,0xA2,0x40,0x8E,0x17,0x40,0xA2,0xFF,0x9A,0xE8)
    for address in [0x2000,0x2001,0x4010,0x4015]:a.emit(0x8E,address&255,address>>8)
    a.emit(0x2C,0x02,0x20)
    for label in ['wait1','wait2']:
        a.label(label);a.emit(0x2C,0x02,0x20);a.ref(0x10,label,True)
    a.emit(0xA9,0,0xA2,0);a.label('clear')
    for page in range(8):a.emit(0x9D,0,page)
    a.emit(0xE8);a.ref(0xD0,'clear',True)
    a.emit(0xA2,0,0xA9,0xF8);a.label('hide');a.emit(0x9D,0,2,0xE8);a.ref(0xD0,'hide',True)
    a.emit(0xA9,120,0x85,0,0xA9,112,0x85,1,0xA9,0x47,0x85,4,0xA9,0xC3,0x85,5)
    a.emit(0xA9,0x3F,0x8D,6,0x20,0xA9,0,0x8D,6,0x20,0xA2,0)
    a.label('pal');a.ref(0xBD,'palette');a.emit(0x8D,7,0x20,0xE8,0xE0,32);a.ref(0xD0,'pal',True)
    a.emit(0xA9,0x20,0x8D,6,0x20,0xA9,0,0x8D,6,0x20,0xA2,0,0xA0,4)
    a.label('background');a.emit(0x8D,7,0x20,0xE8);a.ref(0xD0,'background',True);a.emit(0x88);a.ref(0xD0,'background',True)
    a.emit(0xA9,0x21,0x8D,6,0x20,0xA9,0,0x8D,6,0x20,0xA2,0)
    a.label('stars');a.emit(0x8A,0x29,7);a.ref(0xD0,'no_star',True);a.emit(0xA9,2);a.ref(0x4C,'write_star')
    a.label('no_star');a.emit(0xA9,0);a.label('write_star');a.emit(0x8D,7,0x20,0xE8);a.ref(0xD0,'stars',True)
    a.label('frame');a.emit(0x2C,2,0x20);a.ref(0x10,'frame',True)
    a.emit(0xA9,1,0x8D,0x16,0x40,0x4A,0x8D,0x16,0x40,0x85,2,0xA2,8)
    a.label('pad');a.emit(0xAD,0x16,0x40,0x4A,0x26,2,0xCA);a.ref(0xD0,'pad',True)
    for name,mask,var,bound,compare,change in [('right',1,0,240,0xB0,0xE6),('left',2,0,8,0x90,0xC6),('down',4,1,224,0xB0,0xE6),('up',8,1,16,0x90,0xC6)]:
        end='end_'+name;a.emit(0xA5,2,0x29,mask);a.ref(0xF0,end,True);a.emit(0xA5,var,0xC9,bound);a.ref(compare,end,True)
        if change==0xC6:a.ref(0xF0,end,True)
        a.emit(change,var);a.label(end)
    a.emit(0xA5,1,0x8D,0,2,0xA9,1,0x8D,1,2,0xA9,0,0x8D,2,2,0xA5,0,0x8D,3,2)
    a.emit(0xA9,0,0x8D,3,0x20,0xA9,2,0x8D,0x14,0x40,0xA9,0,0x8D,5,0x20,0x8D,5,0x20,0x8D,0,0x20,0xA9,0x1E,0x8D,1,0x20,0xE6,3)
    a.ref(0x4C,'frame');a.label('interrupt');a.emit(0x40)
    a.label('palette');a.emit(*([1,0x21,0x31,0x30]*4+[1,0x28,0x28,0x28]*4))
    code=a.finish();assert len(code)<0x3FFA
    prg=bytearray([0xEA])*16384;prg[:len(code)]=code
    for i,name in enumerate(['interrupt','reset','interrupt']):prg[0x3FFA+i*2:0x3FFC+i*2]=a.labels[name].to_bytes(2,'little')
    chrrom=bytearray(8192)
    chrrom[16:24]=bytes([0x18,0x3C,0x7E,0xFF,0xFF,0x7E,0x24,0x24])
    chrrom[32:40]=bytes([0,0,0x10,0x38,0x10,0,0,0])
    image=b'NES\x1a'+bytes([1,1,0,0,0,0,0,0,0,0,0,0])+prg+chrrom
    assert len(image)==16+16384+8192
    return image,{'license':'MIT','mapper':0,'PRG_bytes':16384,'CHR_bytes':8192,'CPU_code_bytes':len(code),'reset':a.labels['reset'],'system_RAM_signature':[0x47,0xC3],'input':'D-pad moves ship','audio':'APU disabled; digital silence','commercial_assets_or_BIOS':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args();image,report=cartridge();args.output.write_bytes(image);report['sha256']=hashlib.sha256(image).hexdigest();args.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
