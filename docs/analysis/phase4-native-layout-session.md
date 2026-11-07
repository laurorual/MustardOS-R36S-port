# C103 — sessão usando o layout instalado

Data: 05/11/2026. Código próprio MIT. O C102 instalou as duas entradas que
faltavam na C79. Este incremento remove a necessidade do contorno C99 para
abrir menu → GameBoy → menu, mantendo raiz e dados persistentes somente leitura.

## Implementação

`phase4_native_layout_session.py` verifica a prova C102, o plano e os recibos
nativos0, a linhagem C94/C97 e o mesmo boot/UUID qualificado. A guarda exige
os141arquivos e seus metadados, o template público e o layout instalado:
/etc/asound.conf444bytes/root0644/link único e /mnt/mmc root0755 vazio. Exige
rootext4RO0755, PCM fechado, p1/p3 desmontadas e nenhuma sessão ativa.

O runner C77 é adaptado por substituições finitas somente no módulo de contexto,
namespace privado de evidências e vínculos C102 nos recibos. Fontes e provas
C77/C99/C100/C102 não são editadas. O worker original app-selection é reutilizado
byte a byte. Não transfere etc-view.sh nem usa o worker C99, que exige ausência
dos dois caminhos e deixou de ser apropriado após C102.

Permanece o isolamento por arquivo/caminho do worker original: /etc/asound.conf
recebe bind de uma cópia privada em RAM para o restaurador de áudio e seu hash
original entra no manifesto de restauração. /mnt/mmc é o ponto instalado usado
pelo serviço de armazenamento; não se copia nem se faz bind da árvore inteira
de /etc ou /mnt. O restaurador desmonta as visões e confere os arquivos originais,
mixer, volume, brilho, DRM e WirePlumber. Guardas externas voltam a conferir
layout/arquivos/montagens globais/infraestrutura antes de remover a cápsula.

Não há nova compilação/cópia de código upstream: dispatcher, host/provider4/core
instalados, menu diagnóstico C46 e serviços já aprovados são reutilizados com
integridade conferida. A revisão conjunta de licenças continua pendente; pacote
privado e sem aprovação de redistribuição. Original32 e Steam Deck fora do fluxo.

## Verificações novas

26casos passaram em `native-layout-session/checks.d564ang1`. Cobrem linhagem
real C102/C97, esquema/contador booleanos ou divergentes, recibo incompleto,
RO/fingerprint/infraestrutura/template/delta incorretos, indicação indevida de
montagem/escrita/reboot, boot/UUID divergentes, observação ausente ou com vínculo
C102 errado, guarda de caminhos instalados e uso do worker original. As fontes
e o relatório dos47casos C77 aprovados foram reconferidos; não executados nem
contados como testes novos. Nenhum core/ROM, SSH ou escrita física nesses checks.

## Ensaio nativo

**Aprovado:** `native-layout-session/load.dfmnvdli`, observação
`observe.iv1f5nxf`, boot78/IP192.168.15.8. Usuário confirmou “Tudo certo” para
imagem/direcional/som limpo e audível, restauração Fn+L2 e saída Fn+Start com
retorno ao menu. Registro físico vinculado ao hash da análise técnica concluída;
resposta original mantida privadamente. Nenhum save, Power, volume ou brilho
foi solicitado. O jogo manteve o limite45segundos e encerrou por hotkey,
sem expirar:1160frames. Menu e retorno também tiveram seus prazos/supervisor.

Os três mapas de processo foram confirmados: menu C46, jogo com host/provider4/
core instalados e retorno ao menu. Worker byte-idêntico ao original C77,
etc-view.sh ausente do payload; sem cópia/bind das árvores /etc ou /mnt.
Snapshot e metadados idênticos ao C63, somente duas chamadas status e uma
exportação pelo store instalado, sem QuickSave. Preferências55/70 e mixer/
DRM/brilho/volume/WirePlumber restaurados. O C77 valida também o hash original
de asound.conf após desmontar seu bind por arquivo; a guarda externa confirmou
novamente o arquivo644/444bytes e /mnt/mmc0755 vazio.

Native0/OPERATION0/CLEANUP0, postflight0/mount-health0/cleanup0/stopped-screen0.
RaizRO0755, PCMclosed, p1/p3 desmontadas, UI encerrada, taint0, infraestrutura
PID/starttime e mountinfo global iguais. Cápsula removida e página final
diagnóstica C77 herdada escrita; nenhum jogo ou menu continua rodando.

Analisador C77 congelado reutilizado sem alteração: taxa recente reportada
59,9401Hz, três underruns/1224frames de áudio ausentes no CSV. São agregados;
não se inferem momento, qualidade acústica, média sustentada ou duração real
de saída voluntária. A confirmação de som limpo/audível veio do usuário.
Fechamento offline confere os recibos autênticos desta sessão, preservação de
imagem ancestral/configuração SDK e provas, sem simular nova conexão SSH.
Publicação sanitizada `dist/phase4/native-layout-session`, sem payload de ROM,
estado, imagem, ELF, identidade/UUID real, seed ou chaves. Nenhum ponteiro ou
recibo de etapas históricas foi alterado.

## Limites

Não qualifica boot novo, frontend permanente/autostart, navegador geral de ROMs,
SRAM/novos saves, suspend/energia ou estabilidade longa. Nenhuma migração ou
geração/releitura de seed, avanço de contador ou reativação de.once. Se houver
reboot externo, preparar vínculo explícito ao novo contador/UUID antes de nova
sessão; não fingir continuidade do boot78 nem repetir C94 ou candidata77.
