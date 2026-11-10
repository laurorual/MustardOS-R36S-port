# C26 — buffers e nível do áudio no Panel0

Estado posterior: [C27](phase4-image-volume-calibration.md) concluiu a imagem
privada C25+C26 e calibragem subjetiva do alto-falante. O perfil atual é v3,
codec215/quantum1024, com máximo100 adequado e salvo55/70 preservado. O ganho195
abaixo descreve a aprovação inicial C26 e permanece como evidência histórica.

## Evidências de 31/10/2026

Retomada no C07/boot52, IP192.168.15.8:2222, raizRO/0755, brilho80,
fundação96/payloads/perfil/rede/taint0 válidos. Usuário retornou e autorizou
acompanhamento físico. Nenhum reboot ou token C12/C25 foi necessário.

Sessões C22 instaladas, lease300, dados privados/prefs55/70 e raizRO:

| Sessão/stage em build/phase4/audio-buffers | Variável | Resultado |
| --- | --- | --- |
| run-0001 / session.ppuohabn | baseline | Usuário: chiado alto. Avisos audioconvert já em idle;8 linhas na primeira amostra e48 depois. |
| run-0002 / session.kke0f6_t | force-quantum1024 | Zero avisos de falta de buffers; usuário sem chiado, mas sem certeza de audibilidade. |
| run-0003 / session.630a5n6g | mesmo quantum; monitor de saída | Três toques, usuário sem ouvir. Captura digital provou três WAVs exatos; sem clipping/NaN. |
| run-0004 / session.tx4nqrwp | mesmo quantum + codec195 em vez157 | Usuário: limpo, audível, ainda abaixo do nível usual. Software55 e brilho70 mantidos. |

Cada sessão acima parou/coletou limpa: mixer/DRM/volumes/WirePlumber e brilho80
restaurados, prefs55/70 carregadas/salvas, raizRO, FAT/p3 desmontadas e mesmos
PID/starttime dos daemons de rede. Nenhum ajuste de hardware ficou após o stop.

## Medição e interpretação

Os avisos estavam presentes sem tocar no direcional; não eram apenas artefato
de navegação ou WAV danificado. `pw-metadata` mostrou defaults256/min256/max2048.
O ensaio mudou **somente** `clock.force-quantum` para1024. `pw-profiler` já
instalado mediu período de aproximadamente23222µs no driver, compatível com
1024/44100. Os registros do profiler foram limitados a3s pelo helper existente;
RC124 é encerramento pelo prazo, não falha do áudio. Threads PipeWire e SDL
tinham prioridades RT; não foi necessário ativar RT_PROCESS nos callbacks SDL.

O monitor foi gravado com arecord/PipeWire já instalados, limitado60s emRAM.
O roteamento foi verificado: duas ligações do sink de playback ao coletor,
`stream.capture.sink=true`, sem ligação de microfone. Foram21168000bytes,
5292000 amostras float/2ch/44100, sem NaN/infinito/fullscale. Correlação achou
**três WAVs completos exatamente iguais** ao original convertido PCM16→float,
nos instantes26,6333s/27,7478s/28,8160s, total139182 amostras não nulas.
O pico0,91552734375 coincide com30000/32768 do recurso aprovado.

Isso estabelece integridade até o monitor, não fidelidade da saída analógica.
`monitor.channel-volumes=false`: ele é anterior à atenuação de volume do sink.
Props do sink mostraram channelVolumes0,166375/0,166375 para wpctl0,55. A fonte
WirePlumber do SDK confirma escala cúbica no wpctl e conversão v³ no mixer API:
55% corresponde a cerca de-15,58dB. Isso explica por que um efeito correto pode
ficar muito baixo com o antigo ganho157; não deve ser descrito como perda de
amostras ou como equivalência linear55%.

O ganho195 foi comparado mantendo quantum1024/software55/rotaSPK_HP. A audição
passou para esse ponto de operação. Máximo acústico, faixa completa, fones e
outros painéis continuam não qualificados. Não se aumentou volume persistente.

Referência primária: [propriedades PipeWire1.2](https://docs.pipewire.org/1.2/page_man_pipewire-props_7.html),
além das fontes1.2.8/SDL2.30.12/WirePlumber usadas pelo SDK. Pesquisas por bugs
de SDL3 não demonstraram aplicabilidade a este SDL2; nenhuma biblioteca foi
substituída por especulação.

## Implementação e instalação seletiva

S95 próprio aceita audio_quantum0 (compatibilidade) ou1024. Valida antes de
iniciar core; com áudio ativo, aplica metadata e confere leitura **antes da UI**.
Se houver falha, para o áudio pela rotina existente e não anuncia prontidão.
Metadado pertence ao daemon e desaparece no stop. Perfil privado v2 escolhe1024
e codec195; mantém UIoff, template100/80/policy3 e overrides C22 para55/70/policy0.
O mixer de recuperação C07/core-asound95 não foi alterado.

Receita real/perfil determinístico/post-overlay/guardas/rollback:10 casos.
S95:6 casos com pw-metadata substituído (off, set/readback, erros de set/get,
valor retornado errado e valor não permitido). Transação C24 sobre o plano C26:
14 casos de aplicação/rollback, preservando contador novo e estado privado.

Plano `build/phase4/rootfs-candidate/c26-update.gerwdmdq`, target
`c26-source.ztqxhr7l`. Dez arquivos existentes, nenhum diretório/ELF novo;
fundação permanece96, payloadC22 permanece15, perfil21. Backup10 públicos em
`build/phase4/private/c24-backup.4cea41ut/original-files.tar`,600/parent700,
SHA no descriptor do stage. Counter52/seed/SSH/rede/p3 excluídos do payload.
Aplicação RC0 concluída no52: raizRO/0755, fundação96/payload15/perfil21,
privados e identidades dos daemons preservados, brilho80. Sem token/reboot.
Conferir install-analysis.json; não repetir a aplicação.

**Validação final concluída52/run-0005**, stage session.f7svwv75: C22 normal do
pacote instalado, sem --quantum/--gain do runner. Audit comprovou metadata1024
produzida pelo S95, codec195/rotaSPK_HP e software55; zero avisos de falta de
buffers antes/depois dos dois toques. Usuário confirmou: "Sim, limpo e audível".
Stop/coleta0, mixer/DRM/cache/brilho80/prefs55/70, raizRO, p3/FAT desmontadas,
96hashes/taint0/rede/mesmos daemons e assinaturas selecionadas de erros0 passaram.
Console52 ficou ligado sem UI/worker/arecord/profiler pendentes. Não houve reboot.
O status genérico do coletor não infere qualidade sonora; a confirmação humana
está em physical-installed.json e na análise agregada.

Prova pública `dist/phase4/audio-buffers-correction`:5 sessões,30 casos host,
plano/payload/instalação, fontes e SHA256SUMS conferidos. Não inclui raw60s,
rootfs, blobs, backup ou fingerprint privado. A gravação permanece só em build.
Não repetir baseline ruidosa, monitor60s ou o ajuste já aprovado.

Próximo: composição privada de imagem com C25+C26, sem UI/token de fábrica.
O compositor C23 histórico precisa transportar o S95 novo além do perfil v2
antes da fundação. Este incremento criou target atualizado e instalação
seletiva, sem recompor/bootar uma imagem inteira. Faixa acústica máxima/fones,
outros painéis, coldboot, energia/suspend e longa duração continuam pendentes.

O runner `phase4-audio-buffers.py` separa start/snapshot/monitor/stop/collect,
usa geração+config para ownership e lease do C22. O primeiro upload do monitor
teve LF extra e foi recusado por checksum antes de executar; erro preservado,
serialização corrigida e shell BusyBox/hash conferidos antes da captura.
