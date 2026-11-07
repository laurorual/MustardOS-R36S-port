# Fase 4 — C58: diagnóstico usa o CLI instalado

Em 02/11/2026, o diagnóstico de leitura de saves passou a consumir o
`muos-save-store` instalado no C57. A integração foi validada sem interface
gráfica no R35S, C07/boot69/IP192.168.15.14: o CLI consultou, exportou para RAM
e verificou a geração1 existente. O store permaneceu byte-idêntico ao recibo
C54, p3 foi montada somente RO/noload e desmontada ao final. Nenhum novo save,
instalação, reboot ou teste físico foi necessário neste incremento.

## Implementação

`gb-installed/installed-store.sh` executa somente o caminho absoluto
`/usr/libexec/muos-save-store/muos-save-store`. Antes de cada despacho confere
os quatro hashes C55/C57, modos, owner/group, nlink1 e ausência de symlinks
nos pais. Isso inclui o próprio manifesto, contrato e licença. Exige raiz
RO, cápsula tmpfs/root700, role exatamente loadLF e identidade root600/nlink1
exata, vinculada ao caminho do store. Só aceita `status` e `export` com
aridade exata; exportação tem destino RAM fixo do runtime. Recusa init,
commit, recover, identidades divergentes e qualquer `capsule/save-store`,
inclusive link quebrado. Não há escolha de executável por ambiente ou fallback.

`gb-installed/store.sh` mantém o gate load-only C54 e valida tanto o backend
adaptado quanto o novo dispatcher por hash/tipo/owner/modo/links. O backend é
gerado por `phase4_installed_store.render_backend` a partir dos bytes C53
congelados. Remove prepare/commit e toda transição para montagem RW, restringe
operação a seed/verify e role a load, e substitui somente as chamadas status/
export pelo dispatcher instalado. Os checks de árvore/marker, preferências,
HEAD1/0/2, tmpfs, inspetor e inventário RO vêm do diagnóstico aprovado.
C53/C54 e suas regras de boot permanecem sem alterações.

Os scripts são originais MIT. Foram consultados o backend C53, o gate e o
vínculo de recibos C54, data-functions/card-guard empacotados, mount-namespace,
lifetime lock e o executor limitado já usados pelo C52. Não se recompilaram
CLI, inspetor, runner, frontend ou core; não se alteraram refs, SDK ou imagem.

## Testes de despacho

`checks.x59krv2o` passou34fixtures em container sem rede, com pacote/backend
sintéticos e sem ROM/estado comercial. Cobrem status/export corretos, comandos
mutáveis/argumentos extra/destino incorreto, role/identidade/LF extra, cópia
alternativa na cápsula, arquivo ausente ou adulterado em cada um dos quatro
componentes, modo/hardlink/symlink/pai alias, e delegação seed/verify versus
prepare/commit ou scripts/recibos inválidos. `stat` e `dirname` são os applets
BusyBox AArch64 da árvore C56 executados em A35/QEMU. As fixtures verificam
que recusas ocorrem antes de chamar o backend/CLI sintético.

Uma fixture inicial encontrou a combinação `[ausente] && [sem-link]` sem
saída explícita: em `set -e`, falha no primeiro termo não encerrava a lista.
Os guards compostos do dispatcher agora têm `|| exit64`, e os casos de cópia
alternativa regular/link são aprovados. Nenhum dispositivo foi usado nessa
correção.

## Ensaio nativo sem interface

`run-phase4-installed-store.py` exige `--source-load` explícito, coincide o
recibo privado C54 com a prova sanitizada imutável, confere fontes/inspector e
os hashes do pacote C57. O ensaio mantém o mesmo boot69 do recibo; não relaxa
o adaptador C54 para aceitar novos contadores automaticamente. O inventário
final C54 vincula a geração comercial exata. ROM/core não são enviados, nem
uma cópia ELF do store: apenas scripts, identidade/recibo e o inspetor já
aprovado. O inspetor é o único ELF transferido, sem recompilação.

O lifetime lock e o executor instalado limitado a45s controlam uma namespace
de montagem privada. Como `/run/muos/storage` estava ausente globalmente,
o ensaio monta tmpfs privado sobre `/run/muos` e cria o runtime dentro dele,
sem criar aquele diretório global. A cápsula fica fora desse mount. P3 é
montada em `capsule/data` com ro,noload,nosuid,nodev,noexec, usando as guardas
C20/C22 existentes. Preferências55/70 são conferidas antes da leitura; os
hashes de preferências e store devem coincidir antes/depois.

A primeira rodada `native.8_7554tn` parou no dispatcher por `stat -f` não
compilado no BusyBox1.37 da imagem, antes de chamar o CLI. O trap confirmou
p3RO e cleanup0; rootRO, mounts/infra e ausência de namespaces vivos foram
conferidos, e a cápsula foi removida. O teste de filesystem agora usa
`findmnt`, já disponível e usado pelo diagnóstico. As fixtures finais usam
o BusyBox do rootfs para evitar depender do conjunto de opções GNU do host.
O coletor também passou a aceitar somente os recibos existentes, para permitir
limpeza e diagnóstico de uma rodada incompleta.

Rodada final `native.ewspqvb0`:

- duas chamadas status e uma export pelo CLI instalado, cada uma com pacote
  verificado e sem ELF alternativo na cápsula;
- seed/verify0, HEADcurrent1/previous0/next2, inventário inteiro byte-idêntico
  ao final C54 e entre as duas leituras;
- exportação em tmpfs: PKSTv1, CRC do core, manifesto e assinatura PNG válidos,
  payload do core26861bytes; nenhuma folha comercial foi coletada pelo host;
- preferências55/70 preservadas e montagens de dados exclusivamente RO/noload;
- operação0/cleanup0, rootRO0755/fundação97/taint0/PCMclosed, quiescência,
  infraPIDs/starttime e mounts globais iguais antes/depois;
- p3 desmontada e todos os scripts/identidade/recibos/estado RAM removidos;
  pacote C57 permanece instalado, passivo e byte-idêntico;
- sem UI, jogo, áudio, token C12/C25, reboot, montagem RW ou escrita no cartão.

A geração1 continua somente no cartão128. Original32 e Steam Deck não foram
acessados. A página de diagnóstico anterior permanece na tela. A prova
qualifica o backend sem interface; restauração por Fn+L2 dentro do jogo usando
esse novo despacho será qualificada numa rodada supervisionada posterior.
Não se repetiram as34transações/laboratório C52, áudio, USB ou navegação C54.

## Reprodução e próximo incremento

```sh
python3 port/scripts/check-phase4-installed-store.py
python3 port/scripts/run-phase4-installed-store.py --host 192.168.15.14 \
  --source-load build/phase4/gb-reboot/load.x7a7858i
python3 port/scripts/package-phase4-installed-store.py
```

Não repetir o ensaio por rotina: `latest-native` registra a rodada aprovada.
O empacotador recusa sobrescrever `dist/phase4/installed-store-backend` e
congela somente fontes, backend gerado, checks e recibos sanitizados com
SHA256SUMS. Não inclui ELF, tar, estado/PNG/INI, ROM, identidade privada,
hashes dos bundles comerciais ou credenciais. O `.config` compartilhado do
SDK e as provas C53/C54/C57 são conferidos sem alterações.

Próximo C59: integrar o mesmo despacho na sessão de Game Boy e validar uma
única restauração Fn+L2 com observação física e saída Fn+Start, sem novo save.
Preservar o runner/lifecycle/host/core e o vínculo explícito dos recibos; não
remover a guarda de boot se o console tiver reiniciado. Runtime permanece
RAM, p3RO por padrão, e nenhuma gravação durável é automática. Nenhuma sessão
C59 está armada. Boot da imagem C56, Power/suspend, SRAM/GC, perda elétrica,
continuidade de áudio e desempenho NES seguem separados.
