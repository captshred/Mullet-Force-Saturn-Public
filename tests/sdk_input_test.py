#!/usr/bin/env python3
"""Run the actual pinned SGL poller on a synthetic peripheral buffer.
This catches physical connector layout mistakes without claiming an SMPC test.
"""
from pathlib import Path
import re,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
sdk=root/'.deps/joengine'
assert subprocess.check_output(['git','-C',str(sdk),'rev-parse','HEAD'],text=True).strip()=='556d081146211b6a1cfa6591d70f9487d406758b'
source=(sdk/'jo_engine/input.c').read_text()
start=list(re.finditer(r'void\s+jo_get_inputs_vblank\(void\)\s*\{',source))[-1].start()
body=source[start:source.index('#endif',start)]
assert '__JO_SECOND_MULTITAP_OFFSET' in body
# Keep the pinned poller's constants and body, rather than reproduce its mapping.
constants='\n'.join(re.findall(r'^#define\s+__JO_(?:SIZEOF_6_PerDigital_SIZE_DIV_SIZEOF_INT|SECOND_MULTITAP_OFFSET).*$',source,re.M))
with tempfile.TemporaryDirectory() as tmp:
    fixture=Path(tmp)/'poll.c';exe=Path(tmp)/'input-test'
    fixture.write_text('#include <jo/jo.h>\n#define JO_ZERO(x) ((x)=0)\n'+constants+'\nPerDigital jo_inputs[12];\nextern PerDigital *Smpc_Peripheral;\n'+body)
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-I'+str(root/'tests/input_mock'),'-I'+str(root/'src'),str(root/'tests/input_test.c'),str(root/'src/input.c'),str(root/'src/game.c'),str(fixture),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS actual pinned SGL poll body: peripheral[0]/[15] -> Jo slots 0/6 -> independent players')
