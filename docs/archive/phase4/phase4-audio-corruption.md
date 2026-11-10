# Áudio corrompido relatado no C25/boot50

**Atualização31/10:** [C26](phase4-audio-buffers.md) corrigiu o caminho de bancada
e foi instalado/confirmado pelo usuário no52: quantum1024 antes da UI,
codec195 e volume salvo55, som limpo e audível. Provas em
dist/phase4/audio-buffers-correction. O texto abaixo preserva o diagnóstico
anterior à correção; máximo acústico e faixa completa ainda não aprovados.

## Estado e limites

O usuário confirmou menu visível e D-pad funcionando no boot50, mas relatou
“o audio parece corrompido”. Depois informou ausência e pediu que testes que
dependam dele aguardem seu retorno. Essa restrição vigorou naquela ausência;
foi levantada quando ele retornou em31/10 e acompanhou o C26.
O encerramento por lease e o fallback C07 continuam automáticos e autorizados.
Ambos terminaram: lease50 limpa e fallback51/C07 aprovados. Console ligado,
raizRO, sem UI/token pendente; conservar esse estado até o próximo trabalho.

C25 qualifica seleção/boot único, UI/input, preferências e lifecycle. RESULT0
da sessão/coleta não aprova a qualidade de áudio. O defeito foi observado
nesta rodada, mas ainda não há evidência de que foi introduzido pelo C25.
Nenhuma correção de áudio foi implantada ou outro som disparado pelo auditor.

## Evidência recolhida durante a sessão existente

Stage `build/phase4/rootfs-candidate/c25-physical.qks2rj8_`, arquivos
`physical-observation.json`, `audio-active-audit.*`, `audio-active-graph.json`
e `audio-analysis.json`. Cópias públicas na prova `launcher-once-physical-boot`.
Grafo filtrado por whitelist de propriedades/formatos/buffers: não exporta
credenciais, seed, chave SSH ou estado de rede.

- Volume software0.55, perfil/p3 55/70, raizRO, backend SDL/PipeWire ativo.
- ALSA em RUNNING: MMAP_INTERLEAVED/S32_LE, estéreo44100, period512/buffer2048.
- Nó45 do frontend F32LE/44100/stereo, `node.latency=2048/44100`,
  `node.async=true`, driver35. Sink35 tem `node.max-latency=1024/44100`.
- PipeWire1.2.8 registrou49 linhas `out of buffers on port 0 2` no snapshot,
  de38,20s até137,02s de uptime, além de mensagens suprimidas pelo rate limiter.
  Isso **não** é contagem de xruns ALSA, amostras perdidas ou frames corrompidos.
- O aviso vem de `spa/plugins/audioconvert/audioconvert.c:3034` da fonte de
  PipeWire usada pelo SDK: a fila de saída daquele port não ofereceu buffer,
  apesar de ter dois buffers configurados. O endereço do log ainda não foi
  associado de forma conclusiva a um nó/port do grafo.
- O frontend upstream abre SDL_mixer F32/stereo/44100 com2048 amostras em
  `refs/muos/frontend/common/platform/audio.c:169` e `:198`. O backend SDL2
  2.30.12 usado aqui omite RT_PROCESS deliberadamente porque o callback pode
  alocar/bloquear (`src/audio/pipewire/SDL_pipewire.c:1124`). Não adicionar
  essa flag sem auditar mixer/callbacks.
- Avisos64→2 canais pertencem à enumeração do capture/source inativo; não
  demonstram que playback esteja enviando64 canais. BlueZ/V4L2/logind opcionais
  ausentes também não demonstram a causa do defeito e não reabrem a investigação
  USB já aprovada.
- `pw-top` não está instalado e o kernel não expõe `/proc/PID/schedstat`.
  Essas limitações ficaram nos recibos; nada foi instalado no aparelho/host.

O WAV de navegação instalado mantém SHAadac7879…1bb3ee, o mesmo da adaptação
C06 r4 aprovada: PCM16/44100/stereo/38016frames, pico30000, zero amostras em
fullscale. Os controles de ajuda têm3490frames/pico22154 e também nenhum
fullscale. Métricas foram calculadas offline no target com hashes iguais aos
instalados. Isso não descarta clipping no mixer/codec nem demonstra fidelidade
analógica. Conversão F32→S32 é um caminho esperado, não prova de formato errado.

## Próximo incremento preparado

Priorizar a integridade do áudio antes de promover o novo caminho à imagem.
Preservar 55/70, rota/ganho já aprovados e Wi-Fi-only; não repetir C05/C06 de
ganho, C20 hardcoded60/75, USB ou edição física por hipótese genérica.

1. Inspecionar negociação Buffers/Latency do stream e dos links; mapear o port
   que emite o aviso. Consultar params e estado dos threads na próxima sessão
   já autorizada; usar arquivos de `/proc/PID/task/*` disponíveis em vez de
   depender de pw-top/schedstat.
2. Separar ausência de efeitos e efeitos sob navegação, comparando fila/avisos
   e counters. Não inferir qualidade sonora apenas pelo contador ou status0.
3. Somente com evidência, preparar UMA variável por ensaio (negociação de
   buffers/quantum ou scheduling). Manter overrides RAM, lease, cleanup e
   retorno C07; verificar source/licença/ABI se uma biblioteca for alterada.
4. Validar primeiro em host/ambiente descartável quando possível. A reprodução
   física e o A/B auditivo devem aguardar o usuário avisar que retornou.

Nenhum novo token, launcher permanente, replay de som, mudança de ganho ou
novo reboot para áudio deve ser disparado automaticamente na retomada.
Composição C26 da imagem continua pendente; seu contrato deve conservar C25
sem pedido de fábrica, contador0 e exclusão de seed/chaves/credenciais.
