# C19 — ext4 isolado com raiz somente leitura

Validado em 29/10/2026 no boot40/C07, IP192.168.15.15:2222 com a mesma chave
SSH fixada. A retomada confirmou os SHA256SUMS do pacote de preparação anterior;
os16 testes do store não foram repetidos. Nenhum reboot foi pedido nesta rodada.

## Implementação e escolha

`port/diagnostics/phase4-preferences-ext4.c` é um diagnóstico original MIT.
Consome somente uma imagem regular de16MiB num diretório próprio root0700 em
tmpfs `/run/muos-prefs-ext4.XXXXXX`. Não aceita dispositivo, imagem ou destino
arbitrário; não formata, não altera partições e não remonta a raiz.

O helper cria um namespace de montagem e torna a propagação privada, como já
faz `port/utils/muos-mount-namespace.c`. O padrão também existe no upstream
`refs/muos/frontend/module/musftpjail.c:128–129`; nenhuma implementação upstream
foi copiada. Usa as interfaces loop anteriores ao kernel4.4, não LOOP_CONFIGURE.
Só associa um loop livre0..7 com LOOP_SET_FD, sem substituir associação ocupada.
Confere dispositivo/inode do arquivo, offset/tamanho/flags da associação e usa
AUTOCLEAR como proteção adicional; mantém o fd aberto entre desmontagens.

Antes de chamar o store, confere mountinfo exato: ponto, root/, source, ext4,
major:minor, rw e nosuid/nodev/noexec. Cruza com stat/statfs/statvfs e associação
loop; a raiz precisa continuar RO. Assim, a ausência do mount não deixa o store
gravar silenciosamente no tmpfs que fica por baixo. O binário de produção C19
permanece byte a byte igual ao já validado; nenhuma versão de injeção de falha
foi enviada ao console.

Cleanup desmonta normalmente e libera somente o loop cujo backing ainda
corresponde ao inode/dispositivo próprio. Não usa lazy/forced unmount, não
formata mídia desconhecida e não usa sync global. SIGTERM/INT/ALRM interrompem
o processo do store e passam pela mesma limpeza. Há alarme de45s por execução.
SIGKILL/queda de energia não são simulações aprovadas por esse teste.

`prepare-phase4-preferences-ext4.py` compila no container/SDK existente com
ARMv8-A/Cortex-A35, C11, PIE, RELRO/NOW e warnings como erro. A imagem é criada
no host como arquivo regular e usa features explícitas do ext4 compatíveis com
o kernel4.4. Sua UUID fixa identifica somente o laboratório; não é a UUID de
um volume real. Nenhuma dependência foi instalada no Bazzite ou no R35S.

## Resultados

Oito recusas AArch64/QEMU sem privilégios de montagem passaram: argumentos,
dispositivo em argv, traversal, modo desconhecido, symlink, permissões,
helper ausente e tamanho de imagem incorreto. ELF AArch64/ABI4.4.0/loader e
configbaseline do SDK conferidos. Imagem inicial passou no e2fsck-fn.

Stage de build/testes: `build/phase4/preferences/ext4.33nlfd0g`. A primeira
transferência nativa recusou `tar -z`, opção ausente no BusyBox instalado,
antes de executar ou montar qualquer imagem. Cleanup0 removeu o diretório
próprio. O runner passou a transferir tar simples. Os mesmos binários e
resultados host foram reaproveitados, sem recompilar/repetir fixtures.

Stage nativo aprovado: `build/phase4/preferences/ext4.rtmw052p`, apontado por
`latest-ext4`. Resultados reais:

- mount ausente e backing com inode incorreto: recusados antes do store;
- ext4rw privado com raizRO; defaults100/80 e save60/75;
- unmount→mount: init e load preservaram60/75;
- ext4ro: adaptador recusou save; store direto recusou save/load64;
- novo mountrw: registro60/75 permaneceu válido;
- loop liberado; segundo ensaio cancelado após mount por SIGTERM, cleanup eRC143;
- mountinfo global idêntico antes/depois dos dois ensaios, sem loops associados;
- brilho físico80 antes/depois, rede/55 hashes/quiescência/rootRO/FAT desmontada/
  taint0 mantidos; nenhum helper de áudio ou backlight foi chamado.

A imagem desmontada foi recolhida ao host: `after.ext4`, SHA256
`396775af06ed244a465770877daea25f1b8f69357e58bedb4c8f285c691fb6f1`.
e2fsck-fn offline passou e debugfs confirmou exatamente o registro60/75.
Binários, imagem, mountpoint e diretório RAM foram removidos do R35S.

Isso prova IO nativo ext4 e retenção entre montagens. A imagem em RAM não
sobrevive reboot e o par não foi aplicado ao hardware. C11/C12/perfil/init,
kernel/DTB/módulos/libs/tabela/cartão original32 permanecem intactos.
Persistência real e menu permanente continuam desabilitados.

## C20 — plano do volume real, ainda sem execução

Survey somente leitura no40 coletou o MBR completo512bytes, geometria sysfs e
SHA256 dos primeiros16MiB, após as guardas de cartão/modelo/raiz e55 hashes.
Stage `build/phase4/preferences/layout.ro4dgdtg`. MBR DOS4d554432, p1bootable80/
tipo0c/start32768/len204800 e p2tipo83/start262144/len1048576; slots3/4 zerados.
O primeiro protótipo do planner esperava erroneamente flag0 em p1 e recusou o
survey, sem gerar plano. A flag80 foi conferida no MBR real e no gerador da
imagem anterior; o planner corrigido passou nos oito grupos de validações.

`phase4_userdata_layout.py` agora gera apenas arquivos regulares de revisão:
`mbr.proposed` e `userdata-plan.json`. A diferença é limitada aos bytes478..493
do MBR, preservando todo o restante, inclusive diskid/p1/p2/bootable. P3 proposta:
start1310720/len248561664/tipo83/PARTUUID4d554432-03, até o final alinhado do
cartão. Volume planejado ext4/MUOSDATA/UUID6d756f73-c020-4000-8000-000000000001.

Oito grupos de checks incluem slot já ocupado, drift de p1/p2/p4/diskid,
assinatura/truncamento, GPT protetivo, discrepância sysfs, identidade do prefixo
e geometria sem overlap/overflow. Não há writer/formatter habilitado nesse
planner; `execution_enabled=false`. O backup obrigatório dos primeiros640MiB
contém root/seed/credenciais e deve permanecer PRIVADO, fora de dist/.

O usuário não tem leitor neste computador e ofereceu um Steam Deck via SSH.
Esse é o caminho offline proposto: conferir o host/utensílios primeiro, depois
desligar controladamente o R35S e transferir somente o cartão128. Antes de
gravar: identificar CID/capacidade/MBR/prefixo, recusar filhos montados/holders/
swap/hostroot, produzir backup privado verificado, checks offline dos volumes
existentes e testes de writer/formatter/recuperação em imagens descartáveis.
Não usar o original32 nem executar fsck na raiz montada.

Após dados reais, falta o adaptador opt-in que exija identidade e marker,
integração C11/RAM overrides/policy0/slot speaker e auditoria dos writers ALSA.
Não remover o remountRW privado de C11 apenas porque o laboratório passou.
