# C25 — boot único com a sessão instalada

Atualização: [C30–C32](phase4-irq-rate-negotiation.md) instalou a política IRQ
com fundação97 e aprovação auditiva quente55, porém o áudio voltou a falhar
no56 mesmo com IRQ ativo. Fallback57/limpeza passaram; renegociação de taxa
não recuperou. Consultar o Estado atual do checkpoint antes de agir.

Atualização posterior: [C28/C29](phase4-calibrated-boot-audio-clock.md) validou
boot54 e fallback55, mas o usuário confirmou nova distorção de áudio apesar
do perfil215/quantum1024. Aprovações anteriores abaixo são históricas e não
qualificam áudio após reboot. Estado e investigação atual no checkpoint.

Continuação em31/10: [C26](phase4-audio-buffers.md) instalou/validou a correção
de áudio em sessões normais C22 no52. Fundação continua96 com hashes novos;
estado atual é base C07/52/IP192.168.15.8, UI encerrada/raizRO/sem token.
Os boots48→51 abaixo e suas provas permanecem históricos/imutáveis.

## Estado

Pacote instalado no boot 47/C07, IP 192.168.15.13:2222. Nove arquivos,
duas pastas novas e fundação ampliada de 89 para 96 hashes. Aplicação RC0,
raiz RO/0755, contador 47/0600, brilho 80 e identidades dos daemons da rede
preservados. Nenhum marcador armado ou reboot solicitado durante a instalação.
O boot 47→48 já abriu C25 automaticamente; first paint, run-0001, par55/70,
policy0 e ambas raízes RO passaram no audit nativo. SSH voltou sem intervenção.
A lease terminou com RESULT=0/REASON=lease-completed. Coleta e restauração
passaram: brilho80, mixer/DRM e caches iguais aos originais, par55/70 salvo,
mesmas identidades dos daemons da rede, raiz RO, p3/FAT desmontadas,
fundação96/payloads/perfil válidos, taint0 e assinaturas selecionadas de
kernel/storage0. START/FINAL da FAT foram relidos em RO e são idênticos aos
da RAM. Prova imutável em `dist/phase4/launcher-once-boot`.
O reboot48→49 voltou ao C07 sem UI, grant ou geração de sessão, com recibo
usado48 preservado e pedido ausente. FINAL durável do fallback/readback,
fundação96/raizRO/brilho80/rede/taint0/erros0 passaram. Prova imutável em
`dist/phase4/launcher-once-fallback`.
Não houve confirmação visual do usuário durante a primeira janela de lease.

O plano efetivo está em `build/phase4/rootfs-candidate/c25-update.62_tguvi`.
Backup independente dos dois arquivos públicos existentes em
`build/phase4/private/c24-backup.ib5cqp6l/original-files.tar`, modo 0600,
diretório 0700. O descriptor do plano registra o SHA. Não contém contador,
seed, rede, chave SSH nem dados do p3. A transação conserva os demais 88
arquivos da fundação anterior e instala inittab por último.

## Seleção e sessão

Código original MIT em `port/device/rk-r35s-p0/launcher-once`. O pacote
`muos-r35s-launcher-once` depende de C22, fica desabilitado por padrão e
não instala ações de init sozinho. O preparador executa sua macro real,
insere três linhas revisadas na inittab e recalcula a fundação ao final.
Os dispatchers C07 sysinit/shutdown permanecem; C12 continua inativo.

Antes do C07, `select.sh`, filho de PID1, verifica mídia/kernel/painel,
namespace global e raiz RW. O pedido próprio `/var/lib/muos-diagnostic/c25.once`
deve ser arquivo regular root:root/0600, link único, conteúdo canônico:

```
MUOS-C25-ONCE
BOOT=48
```

O número precisa ser exatamente o contador atual mais um. O seletor move o
pedido para `c25.used.BOOT0048` e sincroniza antes de conceder autorização
em RAM. Pedido ausente seleciona C07; inválido fica preservado, sem UI.
Colisão no destino ou falha de sincronização não concedem autorização.
Nenhum código reconstrói o pedido consumido. O wrapper recusa reentrada
e chamadas por SSH antes de criar estado de seleção.

Após C07 concluir rede, parar entropy e selar a raiz, `session.sh start`
valida relatório C07 sem falhas, hashes e quiescência. Exige a autorização
RAM do contador corrente, recusa outra geração existente e inicia a sessão
C22 instalada uma única vez. A configuração 0600 em RAM habilita preferências
e lease de 180 s, com perfil `/usr/share/muos-r35s-profile`. Defaults globais
continuam enabled0/preferences_enabled0/UIoff. O par esperado neste cartão é
55/70; template C10 global 100/80/policy3 permanece passivo, e C22 aplica
o par do p3/policy0 em namespace privado com a raiz RO.

O worker mantém sua lease e cleanup já qualificados. C25 registra a geração
e confere seu run.conf antes de pará-la; a ação shutdown não encerra gerações
manuais alheias. Há prazo de observação de 330 s depois do ready para detectar
cleanup pendente; status isolado não significa sessão limpa. Sucesso exige
done/result0, ausência de binds/processos, restauração e raiz RO. Não há
segunda inicialização C07/entropy no mesmo boot nem tentativa automática de UI.

No boot imediatamente seguinte, a ausência do pedido seleciona C07, e o
recibo usado do contador anterior permite registrar o fallback. Boots posteriores
continuam C07 sem abrir arquivos C25 na FAT a cada boot.

## Relatórios e recuperação

START e FINAL são produzidos em RAM e gravados juntos somente após a sessão
parar e o p3 ser desmontado. Isso mantém a FAT desmontada durante a UI.
Destino `DIAG25/BOOTnnnn`, arquivos de até 64 KiB, diretório exclusivo, sem
sobrescrever relatórios anteriores. A montagem inicial é RO, exige o DIAG.ID
esperado, então abre RW por tempo limitado, confere cópia, sincroniza e desmonta.
Trap própria tenta desmontar em erro/sinal. O coletor compara novamente os
relatórios em montagem RO posterior. Nenhum seed, chave ou credencial integra
os relatórios públicos. START só é durável ao fim do ensaio; interrupção anterior
pode deixar apenas o recibo de seleção. Queda elétrica durante escrita não
foi qualificada.

O runner `run-phase4-launcher-once.py` separa negative/arm/request/running/
collect/fallback-request/fallback-collect. Armar e solicitar reboot gravam
intenção no host antes do despacho e recusam repetição. Conferir o dispositivo
e esses recibos após uma interrupção, sem repetir arm/request cegamente.
O marcador C12 jamais é usado. Backups C24 antigos continuam independentes.

Rollback deste pacote usa `run-phase4-candidate-update.py rollback --stage`
com o stage C25, **apenas se necessário**, após quiescência e coleta da falha.
Restaura inittab/fundação C24r1 e remove somente os arquivos antes ausentes;
preserva contador e privados atuais. Se o token C25 já foi consumido,
preservar seu recibo. Não restaurar o backup C20 nem recarregar seed no kernel
vivo. Não executar rollback no estado aprovado por mera rotina.

## Repetição visual solicitada pelo usuário

Depois de49 aprovado, o usuário informou que estava ausente e pediu repetir
o teste. Isso autoriza uma nova rodada C25 própria, sem rearmar C12 ou repetir
a instalação. O runner host ganhou `new-trial` e `--trial`: a nova pasta
registra SHA do plano/primeiro fallback, contador inicial e motivo; cada
arm/request mantém seus próprios recibos. As provas48/49 ficam imutáveis.

Rodada efetiva em `build/phase4/rootfs-candidate/c25-physical.qks2rj8_`,
base49/boot50/fallback51. A primeira preparação `.7dehvw3g` parou antes de
remountRW/token: C07 não cria `/run/muos/session`. O preparador agora cria
somente esse diretório RAM0700 quando ausente e recusa link/modo alheio.
Quatro fixtures passaram; erro anterior/razão da retomada preservados no novo
stage. Nenhum código nativo ou arquivo instalado foi alterado. Arm50 passou
com raizRO e o reboot49→50 foi solicitado uma única vez.

A observação solicitada usa somente D-pad, sem Power/volume/brilho/cartão;
lease continua180. Após coleta50 limpa, validar retornoC07/51 sem token novo.

No50, o usuário confirmou imagem/menu e navegação corretos, mas relatou áudio
aparentemente corrompido. A lease/coleta/restauração/readback também passaram;
isso aprova UI/input/lifecycle, **não** qualidade sonora. Prova separada
`dist/phase4/launcher-once-physical-boot` inclui a observação e diagnóstico
somente leitura da sessão existente. PipeWire registrou falta de buffers;
causa ainda aberta em [investigação de áudio](phase4-audio-corruption.md).
Nenhum novo som ou ajuste foi disparado pelo auditor.

O usuário está ausente novamente e pediu que testes que dependam dele aguardem
seu retorno. Não abrir outra sessão sonora nem solicitar botões. O fallback
normal50→51 foi concluído: C07 sem UI/worker/grant/pedido, raizRO/brilho80/
fundação96/payloads/perfil/rede/taint0/erros0 e FINAL durável conferidos.
Prova `dist/phase4/launcher-once-physical-fallback`, com SHA256SUMS verificado.
Console deixado ligado no C07, IP192.168.15.13:2222, sem ação crítica pendente.
Os cinco conjuntos de provas C25 passaram na conferência dos próprios hashes.

## Verificações de preparação

35 casos de política/sessão/arquivo/Kconfig passaram em container: ausência,
formato exato, boot errado, permissões, links, colisão, consumo antes do grant,
sync falho sem rearmar, fallback, chamada manual recusada, início duplicado,
falha de start e ownership do cleanup, whitelist/limite de relatórios, falhas
de mount/cópia/unmount e Kconfig off/sem C12/sem dependência recusada.
Nos casos de sessão e arquivo, somente adaptadores nativos de hardware/mount
são substituídos; o script de orquestração é exercitado com caminhos em tmpfs.
SDK compartilhado permaneceu byte a byte igual ao baseline.

14 fixtures da transação C24 exercitaram o plano C25 real, incluindo rollback
em staging, commit, verificação/remount e recuperação preservando contador novo.
O harness precisou escolher um arquivo já existente nos casos de sibling e
parent symlink: o primeiro arquivo C25 fica numa pasta ainda ausente.
Isso corrigiu a fixture, sem relaxar guardas de produção. O adaptador de
relatórios ganhou trap própria de unmount antes da versão final instalada.

No boot 47, BusyBox nativo validou a sintaxe dos cinco scripts instalados.
Select e start chamados por SSH retornaram 64 antes de criar estado RAM,
marcador ou UI. Provas da instalação e recusas em
`dist/phase4/launcher-once-installed`, com SHA256SUMS e fontes fixadas.

A primeira coleta do boot48 passou na sessão/restauração e releitura da FAT,
mas falhou na última expressão AWK do coletor host: o delimitador `/` do padrão
`I/O error` estava sem escape. O erro original foi preservado em
`first-collection-final-health.*`/`collection-retry.json`. O coletor foi corrigido
com regressão sintética e retomada que compara os arquivos já coletados, sem
sobrescrevê-los. Isso não alterou o código do console nem exigiu novo boot.

Sem novo ELF, flash de imagem, kernel/DTB/bootloader, partição ou uso do Deck.
O target do preparador contém C25; a imagem ext4 privada C24r1 anterior não foi
recomposta nesta etapa. Firmware permanente, cold boot, energia física, áudio
calibrado, bateria/suspend e longa duração continuam fora desta qualificação.
