# C21 — preferências na sessão C11 com raiz somente leitura

Em29/10/2026 foi implementada a opção `preferences_enabled=1` no C11.
Duas sessões nativas no boot42/C07 passaram: run-0002 e run-0003 carregaram
volume60/brilho75 do p3 real, atingiram first paint, confirmaram softwarevolume
0.60 e backlight75, pararam limpas e restauraram brilho80/mixer/DRM/configurações.
A raiz permaneceuRO no namespace do worker e no global. Os55 hashes instalados,
root0755, Wi-Fi, taint0 e montagensglobais foram preservados; p3 foi desmontada.

A implementação está em port/device/rk-r35s-p0/session/preferences.sh, com hooks
no worker e guarda de mount compartilhada com C20. A receita compila o store
MIT de produção sem PREFS_TEST e instala os helpers, mas a opção continua0 no
config padrão. A imagem em uso NÃO foi atualizada: só um pacote temporário em
/run foi executado e removido. C11/C12 instalados, kernel/DTB e perfil originais
continuam íntegros. C12 continua inativo/sem.once, allow_power0; menu permanenteOFF.

## Ordem e limites do adaptador

1. Validar a fonte C10 e os21 arquivos efetivos antes dos overrides dinâmicos.
2. Exigir rootRO0755, Panel0/kernel/cartão corretos, p3 ext4/UUID/label/geometria
   e markers C20. Montar somente no namespace privado, rw/nosuid/nodev/noexec.
3. Usar somente `load` do store existente; não criar/resetar defaults em C21.
   Aplicar volume/brilho e policy0 nas cópias RAM. Reconciliar os slots de volume
   copiados em RAM com o valor salvo para LOAD_SINK_VOLUME não restaurar100.
4. Bindar p3 em /userdata para S90; as pastas de conteúdo MUOS/ROMS seguem o
   contrato S90/frontend. Estado de execução/cache/ready/PID permanece em /run.
5. Isolar emRAM /etc/asound.conf, /usr/share/alsa/alsa.conf, a árvore WirePlumber,
   /root vazio e /opt/muos/log. Não copiar credenciais para o HOME temporário.
   As cópias RAM anteriores de config/device/volume/asound.state permanecem.
6. Iniciar a cadeia aprovada e validar sink interno exato, ausência de fones,
   policy0, cache/config e volume real. Aplicar brilho pelo helper nativo.
7. Somente numa sessão pronta/saudável: parar UI/hotkeys, validar o par limpo,
   cache, brilho físico e volume real sem mute; chamar save ANTES de parar S80,
   que reduz o volume no encerramento. Startup falho não salva preferências.
8. Parar a cadeia e logger antes do unmount p3; desfazer binds em ordem inversa,
   restaurar mixer/brilho/cache/DRM e provar hashes originais. O ramo opt-in não
   remonta a raizRW. O ramo legado0 permanece compatível com C11/C12 existente.

O recorte persiste somente as duas preferências tipadas; não configura áudio
externo, codec, overdrive, boot-policy, seed, rede ou SSH. S90/frontend podem
criar seus diretórios/logs de conteúdo no data, como no contrato upstream;
C21 não transforma essas árvores em backup de configuração global.

A escala de brilho permanece40..160 do Panel0;75 não significa75%. O volume60
é software0..100, com rotaSPK_HP/codec157/157/overdrive0 do perfil aprovado.
Este ensaio não qualifica loudness, fones, shutdown/Power ou suspend.

## Verificações e evidência

- 8 casos de rollback da cadeia e10 casos do controlador C11 no host passaram.
- 14 fixtures de fronteira C21: par/faixas/schema/duplicata/campo extra/blank0/
  entrada shell, volume real divergente/mute/sink ausente. Sem executar entrada
  como shell. O store C19/16 casos não foi repetido: sua fonte não mudou.
- Receita compilada em container/SDK fixado, ELF/loader AArch64 e sintaxe BusyBox
  conferidos; sem instalar dependências no host nem alterar refs.
- Prepare: build/phase4/runtime-session/service.jbuopxfi.
- Checks: preferences/session-checks.xav9zvje e runtime-session/checks.r1dg22ei.
- Nativo: preferences/session-native.urd76rhw; active60/75 nas duas gerações,
  checkpoint60/75 e load60/75 na sessão seguinte com novo mount.
- Provas públicas imutáveis: dist/phase4/preferences-session-native/SHA256SUMS,
  incluindo fonte efetivamente testada, manifestos de build, resultados,
  logs limitados da sessão e saúde final. Sem exportar /root, logs gerais,
  seed, credenciais ou árvore de dados. Pacote RAM removido; gerações públicas
  pequenas permanecem em /run até reboot para diagnóstico.

A primeira tentativa, run-0001, parou ANTES de copiar/bindar/montar: o executor
usou /usr/share/muos-r35s-profile, enquanto a imagem em uso instala o perfil em
/usr/libexec/muos-session/profile. O caminho foi corrigido no executor; não no
cartão. Evidência de falha/result1 retida em session-native.0zkqlqqq e no /run.
Depois de provar ausência de mounts/processos/alterações e lock livre, somente
o ponteiro RAM current foi retirado; o resultado da falha não foi reescrito.
O teste de quiescência dentro da conexão de recuperação ainda retornou1 porque
a própria conexão segurava lifetime.lock; a conexão seguinte passou sem lock
herdado. Nenhuma recuperação exigiu remontar a raizRW ou alterar bytes do cartão.

## Qualificação física e reboot — concluída no incremento seguinte

O primeiro ensaio acima manteve60/75 e não regravou o registro igual.
O incremento seguinte qualificou uma edição REAL pelos botões:60/75→55/70,
checkpoint com novo inode, stop/start e reboot normal42→43→reload C21.
Volume real0.55/brilho70 foram confirmados após reboot; restauração/rootRO/
55 hashes/rede passaram. O valor atual salvo é55/70. Detalhes, comandos e
limites em [edição física e reboot](phase4-preferences-physical.md).
Não repetir store/USB nem diagnósticos hardcoded60/75 no cartão atual.

O Steam Deck já foi limpo, inclusive backup remoto e chave desta tarefa. O
backup privado640MiB conferido continua no host. Recibo em dist/phase4/deck-cleanup
é o estado atual; referências históricas a dois backups estão superadas.
