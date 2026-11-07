# C69 — imagem privada com provider e muxretro integrados

Concluído em 03/11/2026. A composição C67, cujo host e bibliotecas passaram
no ensaio nativo C68, foi serializada em uma nova ext4 de 512 MiB. SHA256:
`b03842ff7ce2a8ddc22948c3bd8002cef832222dd54c3b58e79ae54b587b3e6c`.
Nenhum cartão, console ou Steam Deck foi acessado neste incremento.

O [compositor](../../port/scripts/compose-phase4-provider-image.py) parte da
imagem C56 imutável e escreve somente uma cópia regular nova. Incorpora as
receitas C65/C67 sem os metadados antigos do pacote C60. A releitura integral
confere os 3.386 itens da composição: 27 arquivos e 29 diretórios novos, quatro
bibliotecas existentes alteradas (dois hashes e quatro modos 0755→0644), sem
remoções. Os demais 3.326 itens da base permanecem iguais. Foram conferidos
owner root, modos de 60 inodes e da raiz, e tipo regular/link único das 31
folhas escritas; as quatro folhas substituídas também tinham link único.

`e2fsck -fn` terminou com código zero, sem alterar a imagem. Fundação 97,
payload 15, perfil 21, manifestos de provider/host/store e contrato de boot
passaram antes e depois da extração. Mantidos C07, contador de fábrica zero,
UI e preferências automáticas desabilitadas. A auditoria estática encontrou
307 ELFs AArch64 de userspace e 555 módulos; intérprete, ABI Linux 4.4.0,
release dos módulos e features ext4 continuam os da base aprovada.

A alteração das bibliotecas exigia rever os consumidores. A auditoria leu
NEEDED/intérprete de todos os ELFs e comparou hashes das dependências
transitivas sob o caminho explícito do loader. Quatro programas foram
revalidados em QEMU Cortex-A35: mubattery, muhotkey, muxfrontend e muxretro.
Os quatro passaram pela resolução do loader. Outros 170 programas reutilizam
os recibos C38/C56 somente porque executável e fechamento de dependências
permanecem byte a byte iguais. Isso verifica resolução, sem executar os
programas ou seus serviços, nem qualificar dependências abertas por dlopen.

Stage privado: `build/phase4/provider-image/image.izief28e`. A imagem C56,
a imagem C64, composições e configuração do SDK permaneceram intactas.
O [empacotador](../../port/scripts/package-phase4-provider-image.py) congela
fontes e recibos em `dist/phase4/provider-image`; exclui imagem, ELF, ROM,
estado salvo e dados privados. Os payloads BSP continuam restritos ao uso
privado; este trabalho não resolve suas condições de redistribuição.

Não houve boot desta imagem, reconstrução completa do Buildroot, teste de
reprodutibilidade binária ou integração de FAT/U-Boot em uma imagem de cartão.
A aprovação física C68 pertence aos componentes executados em RAM, e não
constitui aprovação de boot da ext4 C69. O próximo incremento pode incorporar
esta raiz a uma imagem privada completa, preservando os perfis diagnósticos.
