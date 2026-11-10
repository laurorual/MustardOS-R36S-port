# Fase 4 — C63: diagnóstico com host e store instalados

O C63 adapta o diagnóstico para executar `/opt/muos/frontend/muxretro`
instalado pelo C62. Não transporta outro ELF muxretro nem um ELF do store na
cápsula RAM, não cria fallback e não altera a instalação. O backend continua
load-only, com o CLI C57 instalado e seleção C46 em RAM.

Concluído em03/11/2026: o usuário confirmou “Tudo certo” à pergunta explícita
de imagem, direcional, som limpo/audível, restauração Fn+L2 e saída Fn+Start
com retorno ao menu. A qualificação é desse caller diagnóstico limitado,
não de uma sessão permanente ou de inicialização pelo boot.

## Implementação e referências

Foram conferidos o runner/analisador C61 congelados, o plano/manifesto C62,
a receita C60 e o fluxo de lançamento C53. O código original MIT fica em
`port/device/rk-r35s-p0/installed-host-session/` e nos scripts
`prepare/check/run/analyze/package-phase4-installed-host-session.py`, com o
módulo `phase4_installed_host_session.py` para vínculos de recibos.

O renderer gera runner/analisador como delta exato das fontes C61 congeladas.
As guardas C53/C54/C58/C59/C61 não são editadas. O vínculo novo exige C61
aprovado, mesma identidade/assets, mesmo contador inteiro e UUID, além do
recibo e plano C62 exatos e aprovados:13arquivos/13diretórios, zero
substituições, rootRO,105pré-requisitos e ativação manual. Se o boot mudar,
este fluxo recusa antes de alocar a cápsula; não há relaxamento automático.

A lista histórica de assets continua sendo validada primeiro. Antes da
transferência, o renderer remove `muxretro` das listas de arquivos/hashes,
mantém a ausência de `save-store`, troca apenas `app-launch.sh` e acrescenta
o guard `installed-host.sh`. O SHA do launcher consumido pelo seletor passa
a ser o da nova cópia, sem mudar seleção, opções ou lifecycle. O script
original verifica core/ROM e copia o conteúdo em RAM exatamente como antes;
apenas sua linha final passa a chamar o dispatcher fixo.

## Entrada instalada e escopo runtime

`installed-host.sh` recebe somente cápsula e operação `check` ou `launch`.
O root é fixo em `/`; não aceita caminho de executável, core, conteúdo ou
flags por argumentos adicionais. Valida rootRO0755, cápsula tmpfs/root700,
role loadLF/root600/link1, e recusa qualquer arquivo ou symlink `muxretro`
ou `save-store` dentro dela.

Os13caminhos/hashes/modos C62 estão fixados no guard, inclusive o próprio
manifesto. Todos precisam ser regulares, root:root, link1, sem symlinks nos
pais, com pais root:root0755. Assim um manifesto alterado não autoriza
outros bytes. `check` termina sem executar o host. `launch` exige conteúdo
regular400 em storage tmpfs, igualdade com a ROM da cápsula e core/ROM
regulares, antes do exec absoluto com flags fixas fresh/diagnostic-content/
45segundos/hotkey-exit. Não há operação de gravação ou comando configurável.

O preflight e o postflight também conferem o pacote instalado e os105
pré-requisitos C62, além dos contratos anteriores. A biblioteca C46 em RAM
é aplicada aos menus `muxfrontend`; o app herda as bibliotecas padrão do
worker. Esse escopo por componente permanece igual ao registrado no C62.
ROM/core/estado/helpers/runtime continuam RAM, p3 em ro,noload para leitura.
Nenhum novo caller ou dispatcher foi instalado no rootfs.

## Testes offline

Passaram104casos:45de vínculo e59do dispatcher. Cobrem contador/UUID,
identidade/assets/recibos, papel de gravação, implantação inválida,
autostart, hash/modo/path do host, as13folhas com hash/modo/symlink inválidos,
pai inseguro/symlink, hardlink extra, host ausente, alternativas RAM,
argumentos/operação incorretos, rootRW, cápsula fora de tmpfs, conteúdo
divergente/modo/symlink e core ausente. Check válido não executa conteúdo;
launch válido registra exatamente o exec fixo e seus argumentos.

Essas fixtures em container rootless sem rede usam uma raiz sintética, mock
de mounts e um registro no lugar do exec. Não executam muxretro/core ou ROM
comercial. O percurso de pais foi também exercitado com dirname BusyBox
AArch64 via A35/QEMU. A primeira tentativa encontrou apenas um erro da
fixture ao tentar corromper o conteúdo sintético400 num container sem
DAC_OVERRIDE; ela agora muda temporariamente a permissão para a escrita e
restaura400 antes de verificar a recusa por bytes. Nenhuma ação nativa foi
iniciada nessa tentativa. Checks finais em `checks.ju_b1x85`.

Reprodução offline com os mesmos inputs já preparados:

```sh
python3 port/scripts/prepare-phase4-installed-host-session.py
python3 port/scripts/check-phase4-installed-host-session.py
```

O runner requer os recibos explícitos C53 save/load, C54, C58, C59, buildC60,
C61 e implantaçãoC62, além de IP/boot atuais. Não executá-lo por rotina.
Não repetir instalação/rollback ou o teste antigo que exige host ausente.
As provas antigas e o SDK compartilhado permanecem independentes do adapter.

## Resultado nativo e repetição solicitada

A primeira rodada, `load.2_wgmc5y`, expirou no menu sem seleção e sem abrir
o host/jogo. O usuário não viu a janela e pediu repetição, explicitamente
sem aumentar a duração. RootRO, mounts, cleanup0 e remoção de RAM foram
conferidos antes de redisparar. O coletor herdado pressupunha um jogo
concluído e encontrou `store-verify.log` ausente após o cleanup; isso não
foi convertido em sucesso. O recibo separado de timeout registra o ocorrido.
O runtime já estava seguro; a ausência desse log corresponde à transação
de leitura não concluída pelo fluxo de jogo. Essa limitação do coletor em
cancelamentos permanece documentada, sem relaxar validações do ensaio válido.

Na repetição `load.szcr_1jo`, com a mesma duração e mesmo boot70/UUID C61,
o guard validou os13arquivos antes do despacho e novamente no lançamento.
Foi observado `/proc/PID/exe` apontando a **`/opt/muos/frontend/muxretro`**
enquanto o jogo estava ativo. O intent da cápsula também confirma ausência
de entradas muxretro/save-store na lista de ELFs transferidos.

O host saiu por hotkey com954frames/expired0, operação0/cleanup0 e retorno
ao launcher confirmado técnica e fisicamente. O inspetor validou PKST/CRC/
manifesto/assinaturaPNG e26.861bytes do core. O CLI C57 realizou dois status e
uma exportação para RAM; o inventário do store geração1/HEAD1/0/2 permaneceu
byte-idêntico ao C61/C58/C54 e antes/depois. Não houve novo save, commit,
reinstalação, ROM/estado comercial coletado ou reboot.

O CSV registrou cinco callbacks de underrun/2.091frames ausentes, sem
timestamps para localizar a ocorrência. Hz recente59,9401 e média de frame
16,6783ms não são FPS absoluto nem throughput da sessão. Não dividir954 pelo
limite45s, pois houve saída voluntária. A confirmação de áudio limpo é do
teste curto; não qualifica continuidade acústica nem localiza a causa dos
underruns.

Fundação97 e105pré-requisitos C62, treze arquivos instalados, rootRO0755,
taint0/PCMclosed/p3desmontada e quiescência passaram na conferência final.
Prefs55/70, mixer/DRM/brilho/volume/WirePlumber, infraestrutura PID/starttime
e mounts globais foram preservados. Runtime, conteúdo, core, estados e
helpers RAM removidos; host C62 e CLI C57 permaneceram instalados/passivos.
Página finalC63 enviada. Original32/Steam Deck não foram acessados.

Prova congelada em `dist/phase4/installed-host-session`, somente fontes e
recibos sanitizados, com SHA256SUMS e o timeout inicial separado. C61/C62/C60,
os arquivos instalados e o `.config` compartilhado do SDK foram conferidos
intactos. Nenhum frontend/provider ou fluxo automático foi instalado.

## Limites e próximo incremento

O teste supervisionado usa A, Start, direcional, Fn+L2 e Fn+Start, sem novo
save, Power, volume ou brilho. O jogo mantém o deadline declarado45s e runner
externo65s, com menu inicial limitado e retorno automático. Saída voluntária
não qualifica o deadline interno nem permite dividir frames pelo limite.
Logs/metadados selecionados podem ser coletados; estado comercial, ROM,
ELF, PNG, INI, PCM, identidade, hash da ROM e UUID ficam fora da prova pública.

Próximo C64 proposto: compor uma imagem ext4 privada offline com os mesmos
arquivos C56+C60/C62, conferir inventário/readback/fsck/contrato C07 e manter
ativação manual. Reutilizar checks para bytes idênticos e não flashar ou
rebootar o console nessa etapa. Provider completo, frontend permanente,
host após novo boot, boot da imagem, Power/suspend, SRAM/GC/perda elétrica,
continuidade de áudio e longa duração permanecem separados.
