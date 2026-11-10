# C30–C32 — política IRQ e avanço PCM após reboot

31/10/2026. A política IRQ foi implementada e instalada, com backup e aprovação
auditiva em uma sessão no55. **Ela não resolveu o áudio após reboot:** o usuário
confirmou distorção no56, com a política efetivamente ativa. O fallback57 e a
limpeza passaram. Console deixado no57/C07, IP192.168.15.8:2222, raizRO, sem UI.
Não apresentar a ausência de avisos de buffers como aprovação sonora.

## C30: comparação equivalente e ensaio em RAM

O novo modo `--profile-route` do probe de zeros aplicou temporariamente a mesma
rota SPK_HP/215 do menu, com snapshot/restore. `silent.rshsx1ml`, sob
`build/phase4/audio-clock-audit`, mediu aproximadamente44033,7frames/s em
MMAP/S32/estéreo44100, period512/buffer2048. Mixer restaurado byte a byte,
debugfs privado e RAM removidos. Assim, a diferença de rota no C29 foi isolada;
rota e ganho, por si sós, não reproduziram a metade observada no PipeWire.

Foi testada uma única propriedade adicional no sink RK817:

```ini
api.alsa.disable-tsched = true
```

`audio-buffers/irq-session.sh` faz um bind privado da configuração em RAM,
validando origem, namespace, arquivos root600/link único e ausência de montagem
alheia. O worker C22 instalado herda esse bind e mantém seu fluxo normal de
preferências e cleanup; a fonte global não é alterada durante o experimento.

Nove fixtures do wrapper encontraram uma guarda escrita como `! findmnt`:
`set -e` não encerra automaticamente uma lista negada. Foi substituída por
recusa explícita, também no probe silencioso, antes do ensaio no aparelho.
As fixtures cobrem namespace global, links, permissões, conteúdo divergente,
bind existente e unmount do pai mesmo se o start falhar.

A fonte PipeWire1.2.8 em
`build/phase4/graphics-config/output/build/pipewire-1.2.8/spa/plugins/alsa/alsa-pcm.c`
mostra que o modo por timer reduz o período de dispositivos BATCH pela metade
e acrescenta headroom. No ensaio IRQ o próprio backend escolheu period1024,
buffer4096 e headroom0, em vez de512/2048/headroom512. Portanto método de
agendamento e geometria derivada mudaram juntos; não foi isolada uma causa
elétrica ou um único detalhe interno do driver.

| Sessão no55 | Resultado |
| --- | --- |
| session.bvdpctw8 / run-0002 / lease300 | 44099,736frames/s, IRQ efetivo, ganho215/quantum1024/software55; log final sem falta de buffers. Sem audição: usuário pediu repetir. |
| session.fr_x6czx / run-0003 / lease600 | Mesma política em RAM. Usuário: “Ok tudo certo”. Recibo confirmou alvo ainda ativo no recebimento. |

Ambas encerraram/coletaram com result0, mixer/DRM/caches/brilho80 e prefs55/70
restaurados, mesma infraestrutura de rede e configuração global original
SHA324db309… intacta. Diretórios extras da configuração temporária foram
removidos por whitelist. Prova técnica inicial
`dist/phase4/alsa-irq-ram-preparation` permanece sem aprovação auditiva;
a repetição aprovada é separada. A primeira leitura de auditoria usou `jq test`,
indisponível no build sem ONIGURUMA; foi substituída por `startswith`/igualdade,
sem repetir a sessão. Uma coleta iniciada antes de terminar o cleanup recusou
somente leitura; seus recibos foram preservados antes da coleta válida.

## Instalação dirigida

`prepare-phase4-irq-update.py` exige observação auditiva positiva e coleta limpa.
Plano `C30_ALSA_IRQ`, stage
`build/phase4/rootfs-candidate/c30-update.19pb66vi`, instalado RC0 no55.
Foram alterados somente dois arquivos públicos:

- `/opt/muos/device/control/wireplumber.conf`, com a propriedade IRQ;
- `/usr/libexec/muos-session/prerequisites.sha256`, agora97 hashes, incluindo
  explicitamente essa configuração antes do arranque do core.

Perfilv3/codec215, quantum1024, payload C22/15 e perfil21 não mudaram. Não há
novo ELF, serviço instalado, kernel/DTB/bootloader, partição ou flash de imagem.
O gate nativo existente aceita a fundação97 sem alteração de código.

Backup2 públicos em `build/phase4/private/c24-backup.k66d0mis/original-files.tar`,
modo600/pai700, SHA256
`20e645f7f7b35381b307fa79e2dcbc00682f5bb911476c1f127c7c5221b819c4`.
Rollback seletivo usa o stage C30 e conserva contador/privados atuais; não
executar backups C20 antigos nem repetir apply no stage já despachado.

A primeira simulação da transação recusou o caminho de configuração ainda fora
da whitelist. Foi permitido somente esse arquivo exato, com nova recusa para
`opt/muos/device/control/unplanned.conf`. Quatorze casos de aplicação/rollback
passaram, além dos9 do wrapper e9 da candidata. O verificador host mantém a
compatibilidade C27/96 e exige cobertura97 para IRQ, recusando política duplicada,
conflitante, link, hash obsoleto ou fundação incoerente. Prova da instalação e
repetição: `dist/phase4/alsa-irq-installed`.

## C31: validação real após reboot — áudio reprovado

O contrato host C30 verifica instalação/manifest/transação e compara o inventário
com o candidato C27 anterior: somente os dois deltas acima são permitidos.
Não depende de fingir que a imagem privada C27 contém a política nova.
Vinte checks sem hardware validaram esse vínculo, recusas de despacho duplicado
e aceitação de geração manual anterior somente após cleanup0/identidade morta.

Stage `build/phase4/rootfs-candidate/c25-physical.0af7u42a`:
55→56/C25/run-0001/lease180→57/C07. Token56 consumido, native first paint,
55/70/policy0, raízesRO e SSH automático passaram. Após um toque solicitado,
usuário: **“O audio esta distorcido”**. A configuração instalada correta foi
comprovada por hash8bb127e9…, propriedade IRQtrue, codec215, quantum1024 e
software0,55. Mesmo assim, PCM avançou a aproximadamente22050frames/s.
Period1024/buffer4096 estavam ativos e não havia falta de buffers no snapshot.
O exit0 da auditoria de propriedades não aprova a qualidade sonora.

Lease/coleta/restauração0 e relatórios duráveis passaram;57 voltou aoC07 sem
UI/grant/pedido, com fundação97/rede/raizRO/taint0/erros selecionados0. Provas
`irq-launcher-boot-audio-regression` e `irq-launcher-fallback`, sob dist/phase4.
Não sobrescrever a prova de audição limpa no55 ou rotular56 como aprovado.

## C32: renegociação de taxa — hipótese não confirmou recuperação

No57, C22 normal instalado, sem overrideIRQ/ganho/quantum, reproduziu a metade
antes de qualquer toque. Stage `build/phase4/audio-buffers/session.3rmqqwti`,
run-0001/lease600. O helper novo `rate-cycle.sh` executou somente uma troca
daemon-local48000→0. Valida identidade PW/worker e sua trap restaura force-rate0;
há limite externo25s e limite3s para cada comando de metadata. Nenhum tom ou
gravação de microfone foi solicitado.

| Ponto | PCM declarado | Avanço medido |
| --- | --- | --- |
| Antes | 44100 | 22049,450frames/s |
| Forçado48000 | 48000 | 23999,718frames/s |
| Automático restaurado | 44100 | Inválido para taxa: trigger_time reiniciou entre os snapshots. |

Force-rate0 foi confirmado de volta, volume0,55 e quantum1024 mantidos.
Depois da volta houve novos reinícios de PCM. O analisador exige mesmo
owner/trigger/rate e delta positivo antes de calcular avanço; não converte
esses resets em falsa recuperação ou taxa negativa. A hipótese de que apenas
renegociar a família de taxa recuperaria o fluxo não passou.

Parâmetros software efetivos capturados:

| Parâmetro | Valor no PipeWire |
| --- | --- |
| tstamp_mode | ENABLE |
| avail_min | 3072 |
| start_threshold | 9223372036854775807 (LONG_MAX) |
| stop_threshold | 4096 |
| silence_threshold / silence_size | 0 / 0 |
| boundary | 4611686018427387904 |

Os zeros diretos anteriores não reproduziam necessariamente esses parâmetros
software: por exemplo, `aplay` deixava o timestamp desabilitado. Essa é uma
diferença concreta a isolar antes de alterar novamente startup ou kernel.
Não atribuir o contador à frequência elétrica sem medi-la; clk_summary/divisores
do C29 eram a visão do driver/cache, e não prova de relógio físico correto.

Stop/coleta0 e restauração foram concluídos; force-rate era0 antes do stop,
e o daemon foi encerrado. RAM do helper removida. Recibo final em
`session.3rmqqwti/final-health.stdout`:57/C07/rootRO/97hashes/rede e erros0.

## Próximo incremento

Reproduzir os parâmetros software do PCM com zeros e libasound, sem SDL/PipeWire,
comparando uma opção por ensaio (timestamp, avail_min, partida manual/poll).
Reutilizar formato/MMAP/período/buffer/rota já medidos. Se exigir utilitário
novo, construir no SDK isolado e verificar ABI/loader antes de usar apenas em
RAM. Não repetir reboots, calibração ou avisos como substituto dessa comparação.

IRQ permanece uma política experimental instalada, com resultado bom em uma
sessão quente e insuficiente após boot. Nenhuma nova configuração persistente
foi promovida a partir do C32. A imagem privada C27/96 continua histórica e não
contém C30; nova composição97 será necessária depois da correção qualificada.
Original dArkOSen32GB e Steam Deck preservados em toda a rodada.
