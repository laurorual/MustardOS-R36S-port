# C28/C29 — boot calibrado e regressão de temporização do áudio

Atualização: [C30–C32](phase4-irq-rate-negotiation.md) instalou a política IRQ
com fundação97 e aprovação auditiva quente55, porém o áudio voltou a falhar
no56 mesmo com IRQ ativo. Fallback57/limpeza passaram; renegociação de taxa
não recuperou. Consultar o Estado atual do checkpoint antes de agir.

31/10/2026. O boot único C25 com o perfil C27/215 abriu imagem e navegação
corretas, encerrou a sessão e retornou ao C07. **O áudio após reboot falhou:**
o usuário informou “O som está distorcido novamente, mas o resto esta ok”.
A calibração aprovada no52 continua evidência daquele estado; não comprova
áudio correto após boot. Nenhum ajuste de ganho ou correção nativa foi instalado
nesta rodada. Console deixado no55/C07, ligado, IP192.168.15.8:2222, raizRO.

## C28: vínculo da rodada e comportamento de boot

O console estava no53/C07 ao retomar, já com o perfil215 instalado. Não havia
pedido de launcher nem fallback recente: `selected=c07`, `select.result=0`,
`fallback=0`, sem done/result C25, estado válido de um C07 normal.

`phase4_launcher_trial.py` vincula o runner existente à instalação C27,
manifest/deployment/transação, composição privada e equivalência nativa.
Confere os pins de cada conjunto de fontes separadamente e oito arquivos
nativos, incluindo fundação96, payloads, inittab, S95, perfil e certificado.
Não basta aceitar outro nome de experimento ou ignorar hashes C25 antigos.
A rodada registra esse contrato e recusa mudança antes de qualquer despacho.

`run-phase4-launcher-once.py` mantém arm/request/coleta separados, com intenção
persistida no host antes de escrita/reboot, e exige trial próprio para C27.
O native continua C25, lease180, preferências55/70 e defaults globais off.
Vinte e três checks sem hardware validam proveniência, divergências, conteúdo
dos pedidos e recusa de segundo despacho; quatro exercitam o ramo shell real
de estado C07 normal versus fallback limpo/incompleto/falho. Política C25
nativa anterior não foi alterada nem repetida sem motivo.

Primeiro stage `c25-physical.mmdoszo0` recusou o arm por uma condição host ainda
exigir done/result de fallback no C07 normal. A recusa ocorreu **antes** de
remountRW/criação do token/reboot. Leitura posterior comprovou53/C07/fallback0,
raizRO, pedido e temporário ausentes. Não se repetiu o despacho desse stage.
Corrigido o ramo, preservou-se a falha e preparou-se a rodada independente
`build/phase4/rootfs-candidate/c25-physical.mhdme9fw`.

Sequência efetiva:53→54/C25→55/C07. Pedido54 consumido antes do arranque;
first paint/run-0001, software55/brilho70/policy0, ambas raízesRO e rede
automática passaram. Usuário confirmou estar junto do aparelho antes do boot;
três toques no direcional foram o único teste solicitado. Imagem e navegação
passaram; som distorcido foi registrado como falha, sem novos toques pedidos.

Lease54/stop/coleta/restauração result0, preferências55/70, mixer/DRM/caches/
brilho80, daemons e relatórios START/FINAL relidos em FAT RO passaram.
Fallback55 abriu C07 sem grant, geração ou UI; FINAL durável e fundação96/
payloads/perfil/raizRO/taint0/rede/erros selecionados0 passaram. Nenhum token
novo, C12 ou launcher permanente foi habilitado.

## Regressão observada e leitura correta dos registros

A configuração durante a falha era realmente codec215/rota3/SPK_HP,
software0,55 e metadata `clock.force-quantum=1024`. ALSA declarava
MMAP_INTERLEAVED/S32_LE/estéreo44100, period512/buffer2048.

O snapshot inicial do log ainda não mostrava avisos. O pós-navegação mostrou
46 linhas de `out of buffers on port`, com timestamps desde37,265s, próximos
ao primeiro paint37,28s. Portanto zero linhas visíveis na leitura inicial
não é ausência sustentada de falha. Linhas suprimidas não equivalem a uma
contagem exata de xruns. A observação física tem precedência sobre result0
do cleanup e sobre o snapshot inicial.

Duas leituras de PCM na mesma execução:

| Timestamp ALSA | hw_ptr |
| --- | --- |
| 131,354185935 | 2076200 |
| 199,530832384 | 3579496 |

Deltaframes/deltatempo = **22050,014 frames/s**, metade dos44100 declarados.
Isso mede avanço do contador PCM, não frequência elétrica no pino de áudio.
Uma captura limitada3s do profiler foi recolhida; timeout124 é seu prazo
esperado. O profiler também gera Timing*.plot/Timings.html/generate_timings.sh:
a primeira limpeza deixou esses auxiliares, que foram removidos por whitelist
após conferir diretório root700. Nenhum processo ou diretório seu permaneceu.

Provas imutáveis em `dist/phase4/calibrated-launcher-boot-audio-regression`
(`passed=false`, `boot_lifecycle_passed=true`, `audio_passed=false`) e
`dist/phase4/calibrated-launcher-fallback` (fallback passou; áudio permanece
false). Não promover a imagem C27 como áudio qualificado após boot.

## C29: comparação silenciosa e implementação de diagnóstico

Foi criado `phase4-silent-clock-audit.py` com helper original
`audio-buffers/silent-clock-probe.sh`. Confere mídia/kernel/Panel0, raizRO,
quiescência e payload; usa o lock da sessão, wrapper de namespace já instalado,
debugfsRO privado e somente `/dev/zero` como PCM. Cada player tem limite12s,
PID/starttime próprios para cleanup; mixer é salvo/restaurado e comparado
byte a byte. Não abre microfone nem depende de audição ou controles do usuário.
Coleta por whitelist e remove RAM antes da análise dos números.

A tentativa de usar `unshare` recusou sem montar nada porque o comando não está
instalado. O wrapper `/usr/libexec/muos-session/mount-namespace`, conferido pelo
payload, resolveu sem instalar dependência ou novo ELF. Leitura idle55 de
clk_summary foi preservada; ela não substitui medição do fluxo ativo.

Primeira coleta silenciosa `silent.50_22hut` completou os players/restaurou
mixer, mas a análise encontrou timestamp ALSA0: `aplay` não habilita o mesmo
timestamping do PipeWire. Corrigido o sampler para registrar `/proc/uptime`
antes de cada status. A coleta anterior e o erro permanecem, com limpeza de
RAM de recuperação confirmada. Não usar esses timestamps0 como taxa válida.

Resultados seguintes em `build/phase4/audio-clock-audit/`:

| Stage / configuração direta | Frames/s aproximados |
| --- | --- |
| silent.bt7y1e3u / RW S32, buffers default | 44252,7 |
| mesmo / RW S16, buffers default | 44039,6 |
| silent.kjral1dx / MMAP S32, period512/buffer2048 | 44071,3 |
| mesmo / MMAP S16, period512/buffer2048 | 44258,7 |
| mesmo / RW S32, period512/buffer2048 | 44033,7 |

A resolução do uptime é10ms e os snapshots têm intervalo de cerca2s; esses
valores servem para distinguir metade versus aproximadamente44100, sem sugerir
precisão de laboratório. Todos os cinco ficaram a menos1% do nominal.

Entre as duas rodadas diretas, uma sessão C22 normal, sem overrides ou toques,
reproduziu o problema no55. Stage `audio-buffers/session.a6py0d1b`, run-0001:
**22049,590 frames/s** com metadata1024/codec215, sem depender de navegação.
Clocks reportavam I2S11,2896MHz; CKR0x00033f3f indica divisor4 e64 bits/frame,
coerentes com44100. Esses valores são a visão do driver/cache, não medição
elétrica. Apenas mapas de áudio já usados no C05 foram lidos; sem escrita em
registradores ou acesso ao mapa geral do PMIC. Stop/coleta/restauração0,
prefs55/70, brilho80 e integridade passaram.

**Limite da comparação:** os zeros diretos rodaram com mixer original C07
(rotaOFF), enquanto o menu usa SPK_HP/215. Não atribuir a causa exclusivamente
ao PipeWire a partir disso, nem chamar a taxa do relógio físico de provada.
O mesmo formato/MMAP/período/buffer isoladamente não reproduziu a metade.

Houve colisão local de nomes na primeira preparação das provas: o arquivo
host `probe.sh` era também usado para o comando de execução. A fonte enviada
foi recuperada dos heredocs `prepare.sh` e seu SHA conferido contra cada intent,
sem repetir os players. O arquivo agora se chama `native-probe.sh`; comandos
e fontes históricos ficam separados. Prova `dist/phase4/pcm-clock-isolation`
inclui sucessos, falha de timestamp e recuperações, sem áudio raw/credenciais.

## Retomada

Console55/C07, IP192.168.15.8:2222, raizRO0755/counter600, brilho80,
fundação96 e payload/perfil atuais, FAT/p3 desmontadas, taint0 e rede pronta.
Players/UI/PipeWire/profiler encerrados, RAM/debugfs privados removidos.
Recibo final em `audio-clock-audit/silent.kjral1dx/final-health.stdout` sob
build/phase4. Original32GB e Steam Deck preservados; sem novo flash, reboot
além54/55, ELF, kernel, DTB, partição ou mudança permanente de configuração.

Próximo incremento: comparar zeros diretos com **a mesma rota SPK_HP/215**,
mantendo snapshot/restore e buffers iguais. Se continuar correto, isolar a
criação do sink/capture e os parâmetros software do PCM antes de propor um
ajuste de startup. Há motivo concreto para esse diagnóstico; não repetir
calibração subjetiva, baseline ruidosa ou reboots como tentativa cega. Preservar
provas C27 e C28 como históricas, sem sobrescrevê-las ou rearmar C12.
