# C77 — caller com Gambatte instalado

O recorte usa o host/provider instalados pelo C72 e o core instalado pelo C76
em `/opt/muos/share/core/gambatte_libretro.so`. Não transfere host, core ou CLI
de saves para a cápsula. O menu continua com a variante C46 em RAM; o dispatcher
permanece limitado a uma aplicação diagnóstica e a um jogo de até 45 segundos.
Não habilita frontend permanente, autostart, Power ou escrita de saves.

## Implementação e compatibilidade

Fontes em `port/device/rk-r35s-p0/installed-core-session/` e scripts
`*phase4-installed-core-session.py`/`phase4_installed_core_session.py`.
Derivam fontes C73 congeladas, verificadas pela prova histórica, sem editá-las.
A guarda fixa verifica 40 folhas C72/C76, hashes, modos, proprietário, link único
e pais sem aliases; recusa `core.so` na cápsula, inclusive symlink. Caminho,
executável e argumentos são fixos. Manifesto de conteúdo admite exatamente o
caminho absoluto do core instalado e a ROM privada em RAM.

Inspeção somente leitura de `refs/muos/frontend/retro/core/core.c` mostrou
que `core_get_name()` retira `_libretro.so`: a mudança de `core.so` para
`gambatte_libretro.so` altera o prefixo nativo dos saves para `gambatte`.
Os adaptadores novos de `select.sh`, `store-base.sh` e `installed-store.sh`
exportam o snapshot existente para
`/run/muos/storage/pickles/state/gambatte/GB/private`, em tmpfs. Não renomeiam
nem migram o snapshot no cartão. Identidade privada e hash do core continuam
ligados às evidências históricas; os bytes do core C76 são os mesmos C49/C73.
O exportador instalado aceita apenas o novo destino fixo nesta sessão.

O vínculo C77 observa boot e UUID atuais separadamente. Não relaxa as guardas
C73/C68 do boot71. Confere prova C76 e seus nove arquivos adicionais,
132 pré-requisitos preservados, C72/C66/C67 e ancestralidade C63. Se o boot
ainda for72, o UUID precisa ser o capturado pelo C76; outro boot precisa ser
observado e vinculado explicitamente. Nenhum reboot é solicitado.

## Validação

47 casos offline em container sem rede, dispositivos ou execução de core/ROM
passaram: 14 casos de vínculo/mapas e 33 de dispatcher/conteúdo. Cobrem
hashes de recibos, tipos/boot/UUID, host e core ausentes/corrompidos, modos,
symlink/hardlink, pais, manifests, licença ausente, fallback RAM, role de
escrita, operações/argumentos extras e manifesto de conteúdo inválido.
O exec é substituído por registro de argv apenas na cópia descartável.
A adaptação de namespace e restrição seed/verify também têm checks estáticos.

Preflight novo confirmou IP192.168.15.18/boot72, raizRO0755, pré-requisitos e
payload instalado. O dispatcher foi executado nativamente em modo `check`,
com nove arquivos transitórios (duas guardas e sete bibliotecas), sem ROM,
host/core ELF, GUI ou inicialização do core. Confirmou40folhas, depois removeu
a cápsula e reconferiu infraestrutura idêntica e estado quieto.

Sessão física aprovada no mesmo boot72: o usuário confirmou abertura, imagem,
direcional, som, restauração por Fn+L2 e retorno por Fn+Start. Foram1161frames,
saída hotkey/expired0, operação0 e limpeza0; mapas confirmaram menuC46, jogo
com host/provider4/core instalados e retorno ao menuC46. O monitor exige o
caminho instalado do core nos mapas, além das quatro bibliotecas e executável.
Metadata do estado e seed continuam byte-idênticos ao C63; store fez dois
status e um export, sem QuickSave. Inventários antes/depois coincidem com o
snapshot anterior. Preferências55/70, mixer, DRM, volume e wireplumber foram
restaurados. Mountinfo global e infraestrutura PID/starttime ficaram iguais;
rootRO0755/fundação97/PCMclosed/p3off/UIoff/taint0 aprovados. Cápsula removida,
tela final diagnóstica escrita. Nenhum token, reboot ou serviço foi armado.

O CSV reportou core59,8802Hz, três underruns e1499frames de áudio ausentes.
São contadores agregados; não identificam quando ocorreram nem substituem a
confirmação acústica do usuário. Áudio contínuo de longa duração não foi
qualificado. O teste valida a nova abertura e restauração, sem novo save.

### Observações do usuário

A abertura demorou um pouco mais, mas completou normalmente. Não há medição
do intervalo A→primeiro frame; causa e orçamento de latência ficam pendentes.
O novo caller faz verificações adicionais, porém não atribuímos a demora a
elas sem medir. Não repetimos a sessão para investigar essa observação.

A paleta ficou verde. O core é byte-idêntico e os logs mostram a diferença:
C73 `gambatte_gb_colorization=disabled`; C77 `internal`, ambos com
`gambatte_gb_internal_palette=GB - DMG`. A fonte preparada do hostC67 em
`retro/coredef/gambatte.c`, idêntica à referência upstream, fixa `internal`
para o nome `gambatte`. O caminho nativo passa a ativar esse perfil. É uma
diferença esperada de configuração, sem alteração da ROM ou do core; não
forçamos paleta antiga nem gravamos preferência no cartão.

Stages privados: `installed-core-session/checks.sqbqeova`,
`observe.o6ydal_q`, `native-guard.k9k1vgq9` e `load.20cdfwd1`, sob
`build/phase4/`. As primeiras falhas foram da geração/relocação do harness
offline, antes de qualquer execução no console; foram corrigidas e o conjunto
de47passou. Um recibo de observação anterior foi substituído após corrigir a
extração da mensagem de estado (que inclui aspas), sem repetir GUI.

Prova sanitizada em `dist/phase4/installed-core-session`, sem ELF, ROM, estado,
UUID, identidade privada, PCM ou imagem. Recibos autênticos de postflight,
mount-health, cleanup e página final fecham o mesmo boot, sem simular novoSSH.

## Limites

Só o caller diagnóstico e a restauração do snapshot existente entram neste
recorte. SRAM, novos saves persistentes, menu geral de ROMs, frontend permanente,
outros cores, longa duração e perda elétrica permanecem separados. Não se
recompila nem reinstala o core para este teste. Imagens C69/C70 e SDK ficam
preservados. Cartão original32 e Steam Deck não são acessados. Revisão conjunta
GPLv2/GPLv3/MIT pendente; pacote continua privado, `REDISTRIBUTE=NO`.

Próximo recorte proposto: composição de imagem offline incluindo o pacote
Gambatte C75, com manifesto/fsck/readback e preservação da imagem base.
Boot/provisionamento dessa imagem e caller permanente continuam separados.
Medição da latência de abertura pode ser preparada sem refazer esta aprovação.
