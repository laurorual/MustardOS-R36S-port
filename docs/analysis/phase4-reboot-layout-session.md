# C104 — fluxo com layout instalado após reboot

Data: 05/11/2026. Código próprio MIT. O C103 aprovou o fluxo no mesmo boot da
instalação C102. Este incremento confere a persistência do layout e o primeiro
uso de menu/áudio/GameBoy em um boot seguinte explicitamente observado.

## Implementação

`phase4_reboot_layout_session.py` exige a prova C103, observação física e
análise técnica da mesma sessão, recibos de limpeza e fontes preservadas.
Reutiliza o worker original C77 sem visões de diretórios do C99. Regenera a
guarda a partir dos arquivos C77 confrontados à árvore C79, para o contador
seguinte; não substitui o UUID antigo por texto nem relaxa os módulos históricos.
Os recibos novos ligam C103, contador seguinte e UUID atual diferente.

A guarda verifica os 141 arquivos protegidos com metadados, template de áudio,
/etc/asound.conf root0644/444bytes/link único e /mnt/mmc root0755 vazio.
Além da chave fixada do SSH, confere hashes e metadados de quatro arquivos
estáveis de rede/chave, contra o pacote C94 já qualificado por C97. Nenhum
arquivo de seed é lido pelo observador; não repete o teste de entropia C97.
Exige rootext4RO0755, PCM fechado, p1/p3 desmontadas e serviços de UI inativos.

`reboot-phase4-native-layout.py` só aceita o boot C103 qualificado, sincroniza
o plano/claim no host antes do pedido e chama /sbin/reboot normal pelo PID1.
Não usa reboot forçado, sysrq, nova imagem ou token.once. O claim impede
despacho repetido após perda de conexão. Status0/255 do SSH com o marcador
do pedido prova apenas a solicitação; retorno exige a observação seguinte.
O bootstrap C07 executa sua rotina normal já instalada, inclusive contador e
RNG; esta tarefa não invoca geração, carga ou restauração manual de seed.

`run-phase4-reboot-layout-session.py` adapta somente contexto, evidências e
vínculos do runner C77 congelado. Não altera fontes/provas C77/C97/C102/C103,
nem atualiza o layout. Usa host/provider4/core instalados e exportação do
snapshot existente em tmpfs, com restauração Fn+L2, saída Fn+Start e jogo
limitado a 45 segundos. Snapshot e preferências persistentes permanecem somente leitura.
Licenças/referências já revisadas no C103 reutilizadas; nenhuma cópia nova de
upstream. Pacote privado, sem aprovação de redistribuição. Deck não necessário.

## Testes novos

22 casos passaram em `reboot-layout-session/checks.9g4vok9a`: linhagem C103,
transição positiva, recusa de contador igual/antigo/pulado/booleano/string/fora
do limite, UUID antigo/inválido, guarda para boot divergente, observação sem
vínculo C103 ou com hash errado, guarda regenerada com layout/identidades sem
seed, adaptação finita do runner e pedido de reboot normal com sync.
Os 26 casos C103 e 47 C77 aprovados foram reutilizados por integridade, sem
reexecução ou contagem como casos novos. Sem SSH, reboot ou core nesses testes.

## Ensaio nativo

Usuário confirmou presença. Console observado inicialmente no C07/boot78,
192.168.15.8, layout C102 correto e raizRO. Pedido único normal registrado em
`reboot-layout-session/reboot.zsd5kwj4`, claim persistido antes da chamada.
O console voltou no mesmo IP, com C07 pronto e contador79. A observação completa
`observe.itryybk_` aprovou o UUID novo, os quatro arquivos estáveis de identidade,
layout C102, guardas/metadados e infraestrutura no novo boot. O snapshot de
PIDs/starttimes é próprio do boot79; não exige que daemons mantenham os PIDs78.

**Rodada aprovada:** `reboot-layout-session/load.f412eeby`, vinculada à
observação79. Usuário confirmou “Tudo certo” a imagem/direcional/som limpo e
audível, restauração Fn+L2 e saída Fn+Start com retorno ao menu. Resposta e
confirmação física vinculadas à análise desta sessão. Os três mapas confirmaram
menu C46 → host/provider4/core instalados → menu. Worker original preservado,
sem helper/visões de diretórios C99. Não transferiu host/core/store ELF.

1084 frames, hotkey0/expired0, OPERATION0/CLEANUP0. Snapshot e metadados
byte-idênticos ao C63, duas chamadas status e uma exportação, sem QuickSave.
Preferências55/70, mixer, brilho, volume, DRM e WirePlumber restaurados.
Native/postflight/mount-health/cleanup/stopped-screen0: layout C102 intacto,
rootRO0755, PCMclosed/p1p3off/UIoff/taint0, infraestrutura e mountinfo global
idênticos dentro do boot79. Cápsula removida e página diagnóstica final C77
herdada escrita; nenhum jogo ou menu permanece ativo.

Analisador C77 congelado reutilizado: taxa recente59,9401Hz, quatro underruns/
1855frames de áudio ausentes no CSV. Agregados sem localização temporal;
não medem média sustentada, duração voluntária exata ou qualidade acústica.
O som limpo/audível foi confirmado pelo usuário. Fechamento de recibos autênticos
e preservação da imagem ancestral/configuração SDK aprovados, sem simular SSH.
Prova sanitizada `dist/phase4/reboot-layout-session`, sem imagem/ELF/ROM/estado,
UUID/identidade privada, seed ou chaves. Claim e recibo original do pedido
permanecem; return_verified=false no recibo registra o instante do pedido,
e a observação/rodada79 posteriores comprovam o retorno.

## Próximo incremento

Preparar a integração do caller como componente instalado de execução manual,
reutilizando os contratos e o layout agora aprovados após reboot. Criar plano
e testes próprios antes de instalar; autostart e navegador geral continuam
separados. Não é necessário outro reboot/reflash para repetir este resultado.

## Limites

Um reboot adicional ou contador inesperado exige novo plano explícito; não
fingir o boot esperado e não reenviar o pedido por falta de SSH. Não qualifica
queda de energia, reboot frio, variantes de painel, suspend, longa duração,
frontend permanente/autostart, navegação geral de ROMs ou novos saves/SRAM.
Original32 preservado; não reativar.once, C94, candidata77 ou fábrica C100 como
atualização. Em interrupção, conferir claim/recibos/processos antes de agir.
