# C79 — imagem privada completa com Gambatte

Concluído em04/11/2026, inteiramente offline. O
[compositor](../../port/scripts/compose-phase4-gambatte-card-image.py) reuniu
a raiz C78 com o bootchain/kernel/DTB/layout fixados no C70. A imagem raw tem
640 MiB, SHA256
`e9deed97f5d1ae7a9644f0fe20bd8918c7ab3a84c5c172493fcb27912540da4e`.
O gzip privado tem64.988.906bytes, SHA256
`499d48fe64fa90fa4ef51917f39369054bd890314b62d7e2df89511c0bf17946`.

## Composição

O compositor deriva o código MIT congelado do C70, mantendo a criação
exclusiva de arquivos regulares em um stage novo. Não aceita dispositivo de
bloco ou destino externo como argumento. Nenhuma fonte/prova histórica foi
alterada, e nenhum componente foi recompilado.

| Região | Início | Conteúdo |
| --- | --- | --- |
| MBR | setor0 | assinatura4d554432, duas partições |
| idbloader | setor64 | bytes B01/C70 |
| U-Boot | setor16384 | bytes B01/C70,4MiB |
| trust | setor24576 | bytes B01/C70,4MiB |
| p1 |16MiB | FAT32/MUOSDIAG,100MiB |
| p2 |128MiB | ext4 C78,512MiB,PARTUUID4d554432-02 |

Mantidos `ro init=/sbin/muos-ext4-diag`, o Panel0 qualificado e o marcador
`MUOS-R35S-EXT4-P4-B01` exigido pelo bootstrap existente. Kernel, DTB, MBR e
os três payloads do bootchain são os mesmos do C70; os SHA/tamanhos de
Image/DTB embutidos no U-Boot foram conferidos com os arquivos reais.

A raiz inclui o Gambatte em `/opt/muos/share/core/gambatte_libretro.so`,
SHA3e0940da..., com a revisão conjunta GPLv2/GPLv3/MIT ainda pendente. Entre
as seis folhas do FAT, só `PROBE.TXT` mudou: identifica C79/C78 e a presença
do core, sem continuar afirmando que a imagem não contém core. As outras
cinco folhas, incluindo Image, DTB, licença e DIAG.ID, coincidem com C70.

## Verificação e preservação

O verificador C70, cujo fonte permaneceu byte-idêntico, releu MBR canônico,
cinco regiões completas e todos os intervalos vazios. As seis folhas FAT
foram extraídas da imagem final e comparadas por hash com os assets.
As duas partições também foram extraídas sem loop device/mount; seus hashes
coincidem com as fontes. O FAT novo passou no fsck, inclusive após extração.

A ext4 extraída tem exatamente o SHA C78
`a09edf63ac5397b0adc5bdf7d9eb7413f6e02e7963e569b915df0ffe674d08fc`.
Esse vínculo permite reaproveitar o fsck0, a releitura dos3403itens, os
metadados de18inodes, os308ELFs/555módulos, as174resoluções de loader e o
probe/API1 do C78. Não se apresenta uma nova execução dessas verificações
como se tivesse ocorrido no C79. O gzip foi descomprimido e seu fluxo
completo comparado ao hash da raw.

Foram reaproveitados os27casos sintéticos do verificador C70 após conferir
seus recibos e hashes de fonte: offsets, MBR, corrupção, gaps, tamanho,
links e regiões inválidas continuam com o mesmo contrato. Não foi necessário
refazer as fixtures nem o teste físico C77 para estes mesmos componentes.
O conjunto C79 inteiro, porém, ainda não foi iniciado no aparelho.

Ao final, hashes da raw/gzip C70 e da ext4 C78, inventário C78 e configuração
compartilhada do SDK permaneceram iguais. Console, cartões e Steam Deck não
foram acessados. O último estado observado do console é o C77; não houve
nova verificação de IP, boot ou saúde do aparelho neste incremento.

## Artefatos e próximo recorte

Stage: `build/phase4/gambatte-card-image/image.efszbcqw`.
Payloads privados: `muos-r35s-panel0-c79-private.img` e `.img.gz`.
O [empacotador](../../port/scripts/package-phase4-gambatte-card-image.py)
congela fontes e recibos em `dist/phase4/gambatte-card-image`, excluindo raw,
gzip, FAT, bootchain, ELF, ROM, save e dados privados. O pacote permanece
private-only/REDISTRIBUTE=NO; revisão de licenças de boot/GPU/core não foi
resolvida por esta montagem.

Factory permanece C07/contador0, UI/sessão/preferências automáticas off,
sem rede privada, seed RNG, host keys, ROM ou saves. Há somente duas
partições; não há userdata nem resize. C79 não inclui o caller diagnóstico
C77 nem frontend permanente. Não houve flash, provisionamento, novo save,
boot, teste de reprodutibilidade binária, suspensão ou teste de perda elétrica.

Próximo C80 proposto: preparar o plano e as ferramentas de provisionamento
e recuperação para um boot supervisionado, incluindo backup do estado real
do cartão de teste antes de qualquer escrita. A imagem factory de duas
partições não preserva por si só a instalação provisionada e o userdata
atuais. O desenho de implantação deve tratar isso explicitamente, conservar
rede/seed/chaves/contador/saves e manter o original32GB separado. Não há
writer ou operação física armados por este incremento.
