# C68 — host C67 qualificado em RAM

Concluído em 03/11/2026 no R35S Panel 0, IP192.168.15.10/boot71. O usuário
confirmou “Tudo certo” para imagem, direcional, áudio limpo/audível, Fn+L2,
saída Fn+Start e retorno ao menu. O executável C67, diferente do instalado,
foi qualificado em RAM com o provider C65 já aprovado em C66.

ELF qualificado:
cd67ce605cfa406f6084c7348ebf27d475b73340edd981c1343f07b00a995e9d.
O host instalado C62 SHA8d519958... permaneceu íntegro/passivo. Nenhum pacote,
biblioteca, estado, token ou nova preferência foi instalado/gravado no cartão.

## Implementação e vínculo

Código próprio MIT em port/device/rk-r35s-p0/muxretro-provider-session/ e
scripts prepare/check/run/analyze/finish/package-phase4-muxretro-provider-session.py,
com phase4_muxretro_provider_session.py. C66 e seus arquivos/provas são
preservados: o renderer produz deltas exatos de suas fontes congeladas.

O módulo retém todos os vínculos históricos C53–C63 e o provider C65, verifica
a sessão/observação física C66 e o pacote C67, e exige **mesmo contador71 e
mesmo UUID C66**. Uma nova observação somente leitura também fixa IP,
infraestrutura PID/starttime e hashes dos recibos C66/C67. Um boot diferente
é recusado; C68 não adapta esse vínculo automaticamente.

As bibliotecas e os seletores continuam iguais ao C66: menus usam três libs
C65 e libmuxmod diagnóstica C46; o app usa as quatro libs C65. O worker,
supervisor de processos, backend store load-only e ciclo GB mantêm bytes
qualificados. As 66 verificações C66/lifecycle anterior são reutilizadas,
sem repetir ensaios aprovados para esses mesmos componentes.

A única nova entrada ELF fica em capsule/host/muxretro. Esse nome mantém o
processo muxretro sob o cleanup já aprovado; não há entrada capsule/muxretro,
nem ELF save-store na cápsula. O dispatcher mantém a verificação completa dos
treze arquivos instalados e das sete bibliotecas RAM; acrescenta diretório
host root700 sem symlink e ELF regular root:root700/link1 com SHA C67 fixo.
O exec final aponta somente a esse ELF e às flags diagnósticas fixas.

A ausência/corrupção do ELF RAM nunca autoriza usar o host instalado como
alternativa. O pacote instalado é verificado como condição de preservação,
não declarado como executável usado pelo jogo. O guard emite marcador C68
próprio. Version/help nativos usam o novo ELF, e o observador exige
/proc/PID/exe apontando à cápsula e as quatro libs C65 nos mapas.

## Checks e resultado

Passaram **28 casos novos**: 11 de vínculo/sintaxe e17 do dispatcher. Incluem
mudança de boot/UUID/recibo, bool como contador, ambiente inválido, ELF RAM
ausente/antigo/alterado/modo incorreto/symlink/hardlink, diretório inseguro,
pacote instalado ausente, alternativa na raiz da cápsula, role save,
operação/argumento extra e provider corrompido. Fixtures sem hardware/core/ROM;
o exec fixo é registrado, não executado.

Stages em build/phase4/muxretro-provider-session:

- checks.rb4jrjgv;
- observe.jsyy7ay0;
- load.8ef49rho, único ensaio gráfico deste incremento.

O probe das quatro libs e CLI eager do novo host passaram nativamente. Mapas:

    C68_MAP_MENU_FIRST_PROVIDER3_C46
    C68_MAP_GAME_PROVIDER4_RAM_HOST
    C68_MAP_MENU_RETURN_PROVIDER3_C46

O host saiu por hotkey com903frames/expired0, operação0/cleanup0. CLI store
instalado: dois status e uma exportação em RAM; PKST/CRC/manifesto/assinatura
PNG/26861bytes e inventários de store idênticos a C66/C63/C61/C58/C54. Nenhum
novo save, commit ou conteúdo comercial coletado na prova pública.

CSV: Hz recente58,8813, cinco callbacks de underrun e1.637frames ausentes,
sem timestamps que permitam localizar evento acústico. O usuário confirmou
áudio limpo nesse teste curto. A saída foi voluntária: frames/45s não é FPS.
Deadline interno, áudio contínuo, longa duração e limites de desempenho não
foram qualificados.

Final: rootRO0755, fundação97/105pré-requisitos/13arquivos C62 preservados,
PCMclosed/taint0/p3 desmontada/UIoff, prefs55/70/mixer/DRM/volume/brilho/
WirePlumber e infraestrutura PID/starttime/mounts iguais. RAM removida e página
“C68 diagnostic finished”. Não houve reboot solicitado, alteração da imagem,
acesso ao original32 ou Steam Deck.

## Reprodução, prova e continuação

    python3 port/scripts/prepare-phase4-muxretro-provider-session.py
    python3 port/scripts/check-phase4-muxretro-provider-session.py
    python3 port/scripts/run-phase4-muxretro-provider-session.py --host 192.168.15.10 --boot 71 --observe

Observe é somente leitura. A sessão requer observação e checks exatos; não
reexecutar C68 por rotina. analyze/finish conferem resultado/saúde; confirmação
física separada é vinculada ao hash da análise. Prova em
dist/phase4/muxretro-provider-session, somente fontes/recibos sanitizados,
sem ELF/ROM/estados/PNG/PCM/INI/identidade/UUID/hash da ROM. C65/C66/C67 e as
imagens antigas/SDK permanecem intactos.

Próximo C69: imagem ext4 privada com a composição C67, boot C07/contador0,
fsck/readback/owners/modos/manifestos, revisão seletiva de loaders afetados
pelas duas bibliotecas com novos hashes. Reutilizar os demais apenas após
provar bytes e dependências idênticos. Não substituir a imagem C64 ou gravar
cartão; uma imagem raiz local não qualifica boot físico.

Frontend permanente, boot da imagem, Power/suspend, SRAM/GC/perda elétrica,
áudio contínuo e longa duração continuam separados. O usuário autorizou
encadear os incrementos sem parar entre marcos até pedir pausa ou ocorrer
interrupção do limite; registrar cada conclusão no checkpoint.
