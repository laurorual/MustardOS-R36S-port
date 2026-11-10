# C24 — instalação seletiva e primeiro boot do candidato

Continuação concluída em [C25](phase4-launcher-once.md): fundação ampliada
para96, boot único48/fallback49 e repetição visual50/fallback51 aprovados para
UI/input/lifecycle. Áudio corrompido relatado no50 continua pendente. O estado
atual é C07/51 sem token, com raizRO; consultar o checkpoint antes de atuar.
Os89 hashes e próximos passos abaixo descrevem o marco C24 histórico.

Em 30/10/2026, o candidato C23/C22 foi instalado por arquivos no cartão de teste
128 GB, com backup e rollback preparados. O R35S passou a iniciar diretamente o
C07, sem executar o seletor C12. Após corrigir uma dependência de umask no C07,
o boot 47 passou sem intervenção posterior: rede/SSH com a chave fixada, raiz
RO0755,89 hashes de fundação, payload15, perfil C10 e taint0.

O original dArkOSen32 não foi usado como destino. Não houve flash de imagem,
reparticionamento, troca de kernel/DTB/bootloader ou escrita no p3. O par55/70
continua no MUOSDATA. Os logs normais C07 na FAT foram produzidos pelos boots;
a FAT terminou desmontada. Os defaults da sessão/UI continuam desabilitados.

## Preparação e transação

O processo interrompido anterior já havia concluído C23. Seus hashes de fonte,
provas e imagem foram conferidos antes de continuar. A conexão no novo IP
192.168.15.13:2222 confirmou boot45/C07/rootRO/55 hashes e quiescência.

O plano compara o aparelho com os21 arquivos C10 e os componentes C23, não apenas
com o diff da imagem-base. Isso capturou templates que haviam sido alterados na
bancada. Foram selecionados56 arquivos,25 diretórios novos e18 arquivos já iguais
que não precisavam de escrita. Counterfactory0 e todos os caminhos privados,
seed, chaves, rede e p3 ficaram fora do conjunto de escrita.

Os21 arquivos originais existentes foram copiados por uma lista explícita e
conferidos contra hash/modo/UID/GID antes de qualquer escrita no aparelho.
Backup privado independente, sincronizado no host:
`build/phase4/private/c24-backup.1dagpi05/original-files.tar`.
O SHA está no backup-descriptor.json de update.dbsu4g2h; não exportar o backup.
Ele contém somente os originais da transação, sem seed ou credenciais.

A transação valida mídia/kernel/modelo, raizRO, partições, estado C07/entropy
stopped, ausência de UI/mounts, hashes anteriores e espaço livre. Adquire o lock
de sessão. Todos os siblings novos são preparados e conferidos antes de substituir
o primeiro arquivo; bootstrap e inittab ficam por último. Configurações/arquivos
privados são acompanhados por um fingerprint agregado apenas emRAM; os bytes
não são exportados. Há rollback em EXIT/sinal, inclusive se o remount final falhar.

O rollback restaura apenas os arquivos/modos da lista e remove somente arquivos/
diretórios comprovados ausentes. Preserva o contador e o estado privado ATUAIS,
mesmo depois de outro boot. Não restaura um seed antigo. A instalação é detached,
com recibo de conclusão: perder a conexão não autoriza repetir a transação.

16 casos da transação real passaram em fixtures, incluindo falhas no staging,
commit intermediário, bootstrap/inittab, verificação e remount final. O primeiro
harness não tinha acesso aos diretórios privados do host e outro excedeu o prazo
por criar um processo por arquivo. O mapeamento de usuário foi corrigido sem
abrir permissões; o inventário passou a usar hashing Python. Esses problemas
ficaram apenas no container; nenhum deles executou escrita no aparelho.

A instalação no45 passou RC0, retornou a raizRO e confirmou todos os89 hashes,
payload15, fingerprint privado idêntico e mesmos PID/starttime de udev/Wi-Fi/
DHCP/SSH. Stage update.dbsu4g2h. Provas congeladas em candidate-update-installed.

## Primeiro retorno e causa da divergência

O reboot normal45→46 voltou com SSH/rede/rootRO e todos os89 hashes corretos.
A verificação completa recusou o modo do contador: boot-seq tinha virado644.
O seletor C12 antes fornecia umask077; o caminho direto herdou022 do init.
O C07 original criava boot-seq.tmp sem fixar seu modo e o renomeava.

Foi restaurado SOMENTE o modo600, sob guarda de mídia/counter46 e remountRW
limitado, com hash dos bytes igual antes/depois e raizRO ao final. Não houve
reset do contador, reload de seed ou outro reboot durante esse reparo. O gate
89 passou após a correção. Esse retorno não é registrado como boot totalmente
aprovado sem intervenção; o diagnóstico e o reparo estão nas provas r1.

## C24r1 — correção e boot47

O C07 agora define sua própria umask077 e aplica chmod600 ao tmp antes do mv.
Sete regressões exercitam o writer real com umasks000/022/077, tmp666, contador
inválido/exaurido e controle antigo que reproduz644. Todos passaram.

Uma segunda transação atualizou apenas muos-c07-run e seu hash no manifesto89.
Backup de dois originais em private/c24-backup.d3oxb7f_/original-files.tar,
com descriptor no stage update-r1.zoj0rcgv.13 fixtures passaram, incluindo
DIRS vazio e recuperação preservando contador posterior. O contador continuou46
nos dois lados da aplicação, com privados intactos, mesmos PIDs de rede e rootRO.

O reboot normal46→47 passou na primeira verificação: contador47 com modo600,
C07 direto sem /run/muos/selection/mode, gate89/payload15/perfil válidos, rede
no mesmo IP/chave, brilho80, rootRO0755, taint0 e zero assinaturas selecionadas
de erro kernel/storage. Nenhuma reconexão física do dongle foi solicitada.

Provas imutáveis com SHA256SUMS:

- dist/phase4/candidate-update-installed — instalação inicial e16 fixtures.
- dist/phase4/candidate-update-r1-installed — dois arquivos,13 fixtures e7 regressões.
- dist/phase4/candidate-update-r1-boot — boot47 e diagnóstico explícito do boot46.

Os diretórios RAM da instalação/backup desapareceram com os reboots; os backups
independentes permanecem privados no host. Não repetir apply ou reboot-request.

## Imagem privada atualizada

O compositor também passou a incorporar o C07 corrigido, para não recriar o bug.
Novo candidato privado: composition.0bpyh9h_/images/rootfs.ext4, SHA256
2e9c572f9fbfbf5782e48b3b08d12a0aa1ebe7ee09fe649d502ac870b3e84fb0.
Fsck/releitura integral/305ELF+555módulos/172loaders e14 fixtures passaram.
C07 e fundação89 dessa imagem correspondem aos instalados na revisão r1.
A imagem inteira não foi gravada ou inicializada; seu contador0 é apenas um
template de fábrica. A imagem C23 r0 anterior é histórica e não deve ser promovida.
Provas sem imagem/blob: dist/phase4/candidate-update-r1-rootfs.

## Recuperação preparada e próximo incremento

As ferramentas aceitam recuperação explícita por stage. Não executar no estado
aprovado: primeiro seria revertida r1, depois a transação inicial, se necessário.
A ordem preserva os estados intermediários conhecidos. O caminho foi testado em
fixtures, não foi necessário executá-lo nativamente. Estados parciais inesperados
são recusados; perda elétrica durante commit e recuperação sem SSH não estão
qualificadas. Original32 e backups independentes continuam preservados.

Próximo: desenhar um ensaio de boot próprio, de uso único, que invoque a sessão
C22 instalada com preferências e lease, mantendo retorno C07 no boot seguinte.
Não rearmar C12 ou habilitar menu permanente. Os preflights novos devem usar o
contrato direto C07/89 hashes, sem depender do pacote/marcador C12 antigo, retido
inativo para rollback. A qualificação física55/70 e sua retenção já foram aprovadas;
não pedir que o usuário repita a mesma edição ou reinicie novamente sem motivo.
