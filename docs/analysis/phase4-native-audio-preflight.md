# Fase 4 — C05: preparação de áudio, somente host

**Estado: assets/probe preparados e auditados no host; sem payload gravável.**
Rodada limitada pelo saldo de 7% informado pelo usuário. Não houve SSH,
acesso ao console/cartões, instalação, alteração do rootfs ou boot novo.
C04 permanece o último marco nativo aprovado.

## Preparado

O [preparador](../../port/scripts/prepare-phase4-audio-preflight.py) exige
o blueprint C04 `native-frontend.urej9y1t` íntegro e sem seed. Reutiliza os
três bipes de `dist/phase4/core-native/core-tone.wav`, SHA256
`959fcac27fe4bb517ea946d3725857c7fa01b61008c1363d6fdda3dfa96c43e8`.
WAV PCM S16_LE, estéreo, 48 kHz, 144000 frames/3 s. Sem gerar outro sinal
ou importar binários Debian.

O [probe](../../port/device/rk-r35s-p0/audio-diagnostic/probe.sh) é guardado
por root, kernel próprio e marcador C05 ainda ausente no cartão. Exige
core/audio prontos e UI ausente, valida o sink real RK817 e usa
`aplay -D pipewire` limitado a 12 s. Captura antes/durante/depois: Playback
Volume, Playback Path, Headphone Jack, volume de software e hw_params do
PCM. Não escreve explicitamente no ganho do codec nem no volume de
software. Isso não significa que o stack nativo deixe a rota/mixer intactos.

QEMU Cortex-A35 passou em sintaxe do shell, loader de aplay/amixer/wpctl e
`aplay --version`. O ELF do plugin ALSA/PipeWire foi registrado. Esses
checks não abrem PCM real, não testam áudio, não verificam volume audível
e não validam o ciclo completo de startup/stop do futuro runner.
O arquivo `c05-core.conf` com audio1/input1 é apenas um asset para futura
montagem temporária; não foi instalado nem ativado.

Evidência de integração a respeitar:

- `usr/libexec/muos-core-lifecycle` no C04 lê `/etc/default/muos-core` no
  start e retorna imediatamente se core/ready já existe. Portanto trocar
  audio0→1 depois do start não inicializa o áudio.
- O bind temporário de configuração precisa vir **antes** de S95, mantendo
  áudio desabilitado no arquivo persistente e removendo o bind após stop.
- `refs/muos/internal/script/init/S80pipewire.sh:30` lê políticas de volume;
  sua inicialização pode mudar a rota/volume. Capturar ALSA antes de iniciar
  o core, durante o PCM e após a parada, sem assumir equivalência com o
  kernel instalado.
- Sink esperado, já validado no kernel instalado:
  `alsa_output.platform-rk817-sound.playback.0.0`. Revalidar no novo kernel.
- `phase4-core-audio.md` registra audibilidade baixa em testes anteriores,
  inclusive com software unity e Playback95. Esses ganhos não representam
  dB calibrados nem justificam elevar o codec ao máximo. O preset35 pode
  tornar o primeiro probe muito baixo; decidir o nível diagnóstico e o
  critério de repetição antes do ensaio com o usuário.

## Retomada após o reset

1. Ler C04 e este relatório, conferir `latest-audio-preflight` e checksums.
   Os assets são reutilizáveis; não repetir preparação só para retomar.
2. Integrar runner/bootstrap/marcador C05, usando cadeia C02 com audio1 e UI
   desligada. Não incluir frontend nem hotkeys neste primeiro recorte.
3. Planejar cleanup em todos os erros: parar player/amostrador e serviços
   pelo caminho nativo; remover bind core, sync/root ro e salvar logs em
   DIAG07/BOOTnnnn, preservando DIAG04–06. O probe sozinho não faz isso.
4. Adaptar instalador **a partir dos preimages C04**, incluindo assets do
   áudio e guardas de identidade. O instalador atual não aceita C05.
   O WAV tem 576044 bytes, acima do limite atual de assets de 128 KiB:
   a exceção futura deve ser restrita a esse caminho, tamanho e hash.
   Coletor/analisador também ainda não aceitam C05.
5. Auditar imagem host sem seed, shell/loader/fsck, lifecycle/falhas e
   publicar prova pré-boot antes de qualquer escrita. Nunca clonar a raiz
   viva, ler/copiar/hashar seed ou substituir estado privado.
6. Com margem para ida/volta e correção, confirmar usuário disponível,
   saúde/identidade da mídia por SSH, instalar só no secundário e conferir
   fsck. Original de 32 GB fica guardado durante o boot, dongle fora.
7. Testar bipes, transcrever falhas, retornar ao dArkOSen, coletar/analisar e
   conferir saúde antes de encerrar. Exit0 do player não prova audibilidade.

Permanecem pendentes frontend sonoro/hotkeys, shutdown normal, rcS completo,
conteúdo, rede, outros painéis e estabilidade prolongada. Provider privado
mantido; relatório único de licenças ao fim do projeto, como solicitado.

Preparação reutilizável: `build/phase4/linux-diagnostic/audio-preflight.r9ks9vw5`,
ponteiro `latest-audio-preflight`. Prova imutável, com assets/fontes e
checksums: `dist/phase4/native-audio-host-preflight/`. Nenhuma operação
crítica ou processo de build ficou ativo ao encerrar.
