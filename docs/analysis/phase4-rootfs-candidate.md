# C23 — composição privada do rootfs com C10/C22/Wi-Fi-only

Em 29/10/2026 foi composto um candidato ext4 de512MiB apenas no host. A origem
é a imagem C07 limpa já auditada; foram aplicadas as macros reais de instalação
de C10, C22 e Wi-Fi-only, seguidas do hook C10 após os pacotes/overlays da base.
Os hashes de fundação foram gerados DEPOIS das alterações, sem promover o
manifesto histórico de um deployment antigo a manifesto da nova imagem.

Não houve instalação, reboot ou escrita no R35S. Ele foi conferido no boot44,
C07 saudável, com o original32 preservado. P3 ficou desmontada; o par salvo
continua55/70. Nenhum seed, chave privada, credencial Wi-Fi ou cópia da raiz viva
foi usado para construir a imagem. A chave pública de autorização já presente
na base C07 permanece; isso não substitui o provisionamento privado posterior.

## Artefato e origem

Imagem privada:
`build/phase4/rootfs-candidate/composition.rtvw4swv/images/rootfs.ext4`

SHA256: `0ffcffff331eb07de7ecae668837fefd1fe87ee34114feedffe9e85e153d3dad`.
ROOTFS,536870912bytes, raiz0755; recursos ext4 compatíveis com o BSP4.4.
Não é uma imagem de cartão completo: não contém MBR, bootloader, kernel/DTB
novos, FAT ou p3. Esses componentes não foram alterados neste incremento.

A composição usa a imagem limpa network-recovery.zz7sq2ve, cujo hash é
6ac2ec0a3414bd243c0a43afad5e4f1fc86648d722299e356298b981bc18e83b,
ancorada no manifesto congelado network-recovery-preboot.54 dos55 arquivos da
fundação instalada correspondiam à base; a diferença era a inittab com seletor
C12. O candidato mantém despacho DIRETO C07 e não inclui o pacote muos-boot.

C22 vem de service.wjbd9ueq, ancorado em session-package-independent; perfil
C10 e Wi-Fi-only também foram conferidos contra suas receitas/provas aprovadas.
A imagem foi modificada como arquivo regular com debugfs, sem montar partição
ou acessar dispositivo de bloco. As estruturas especiais/permissões da base
foram preservadas, e a imagem foi relida integralmente em uma árvore nova.

O GPU R13 existente na base mantém o uso privado e as pendências de licença já
registradas em port/packaging/pending-licenses.json. A imagem permanece em build/;
somente relatórios, hashes e fontes originais foram congelados em dist/. Não
foi feita redistribuição do rootfs ou dos bytes GPU.

## Contratos finais

- Perfil C10:21 arquivos conferidos após o hook; UI disabled, templates estáticos
  volume100/brilho80/policy3. Os valores55/70 pertencem ao p3, não à imagem.
- Runtime C22:15 componentes cobertos por payload.sha256, guarda local e
  configurações enabled0/preferences_enabled0, lease180.
- Fundação:89 caminhos recalculados na árvore FINAL, incluindo inittab C07,
  defaults, utilitários, libs e novo gate de bootstrap. A configuração da sessão
  aponta para esse manifesto novo em usr/libexec/muos-session/prerequisites.sha256.
- Nenhum menu ou sessão inicia automaticamente. Inittab usa apenas o caminho
  C07 aprovado, sem rcS/rcK genéricos, S98/S99 ou seletor C12.
- Wifi-only é aplicado pela receita; não houve repetição de ensaios USB.

## Incompatibilidades encontradas e corrigidas

O bootstrap antigo exigia audio0, incompatível com o template C10 audio1.
O novo bootstrap carrega muos-candidate-boot-checks e exige defaults de sessão
OFF, UI OFF, template C10, despachos C07 e hashes da fundação. Isso permite
manter audio1 como template passivo, sem iniciar S95/áudio no caminho C07.

A imagem C07 limpa também não continha var/lib/muos-diagnostic/boot-seq, que o
antigo instalador dirigido provisionava fora da imagem. O candidato contém o
template de fábrica: diretório root700, boot-seq root600 com0. O gate aceita
contador vivo válido, como44, mas ele não é incluído no manifesto imutável.

A primeira composição g3whpkgy passou em fsck/releitura/ABI, porém ficou
SUPERADA por essas falhas de contrato; há superseded.json e ela não foi
promovida a prova final nem executada. Tentativas7sj2cd1u/v2_bb4ig pararam no
host por caminhos de utilitários assumidos incorretamente; o compositor passou
a localizar os utilitários reais na árvore. Nenhuma tentativa tocou o cartão.

## Verificações

- Instalação pelas macros reais e aplicação final dos21 arquivos C10.
- Nova fundação89 e manifesto C22/15 válidos antes e depois da imagem.
- Fsck offline0, raiz0755, inventário completo de arquivos/modos/links relido
  da imagem igual ao planejado.93 entradas alteradas/adicionadas:64 arquivos e29 dirs.
-305 ELF userspace AArch64 e555 módulos ET_REL da revisão4.4.189-muos-r35s-p4;
  interpreter correto e nota ABI Linux4.4.0. Kernel/módulos não foram recompilados.
-172 executáveis dinâmicos resolveram suas dependências pelo loader final sob
  QEMU/Cortex-A35, sem executar os serviços ou init do destino.
- Sintaxe BusyBox e recusa64 do bootstrap fora de PID1; gate de contrato testado
  antes/depois da extração. Isso não equivale a um boot real do candidato.
-14 casos de validação/recusa: autostart, preferences permanente, despacho rcS,
  seed, chave privada, helper alterado, fundação stale, escape de manifesto,
  contador ausente/corrompido, template áudio antigo e controles positivos,
  inclusive contador vivo44. Fixtures descartadas, árvore/imagem originais intactas.
- SDKbaseline e imagem base permaneceram com os mesmos bytes. Não houve rebuild
  completo do Buildroot ou qualificação de reprodutibilidade bit a bit da ext4.

Stage de checks: rootfs-candidate/checks.6eacier0.
Provas imutáveis: dist/phase4/rootfs-candidate-composition, com SHA256SUMS,
inventário completo, plano de diferenças, logs, fontes e manifestos. A imagem
privada, blobs, credenciais/seed e backups estão explicitamente excluídos.

## Próximo incremento

Preparar um plano de instalação seletiva e recuperação para o128, ANTES de
qualquer escrita, sem substituir p3 ou restaurar a raiz inteira sobre o sistema
vivo. Preservar o contador real44 e os arquivos privados existentes de SSH,
rede e seed; não instalar o template de contador0 por cima do cartão em uso,
pois os logs FAT antigos poderiam colidir. Nunca recarregar seed no kernel vivo.

O novo caminho direto C07 também não publica o marcador RAM do seletor C12.
As ferramentas de preflight/retorno do novo ensaio precisam reconhecer o contrato
C07 independente, sem depender de muos-boot ou de /run/muos/selection/mode.
Definir verificação e rollback por arquivos/modos/hashes antes do primeiro boot
real do candidato. Não rearmar C12 antigo nem habilitar menu permanente. Este
incremento termina com a imagem no host e o estado aprovado do aparelho intacto.


## Continuação C24 em30/10 — substitui o próximo incremento acima

A instalação seletiva e os boots45→46→47 foram executados em [C24](phase4-candidate-update.md).
O primeiro retorno revelou uma dependência de umask: o C07 direto criava
counter644, enquanto antes C12 herdava077. C24r1 corrigiu o próprio C07 e o
boot47 passou sem reparo. Novo compositor incorpora essa correção; o candidato
mais recente é composition.0bpyh9h_, SHA2e9c572f9fbfbf5782e48b3b08d12a0aa1ebe7ee09fe649d502ac870b3e84fb0,
com provas candidate-update-r1-rootfs. A imagem rtvw4swv descrita neste histórico
não deve ser instalada isoladamente nem usada para reverter o C07 corrigido.
