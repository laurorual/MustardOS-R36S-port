# Guia de instalação

O MustardOS para R36S/R35S é um **port não oficial**: a equipe do
MustardOS não dá suporte a ele. Dúvidas e relatos de problemas vão
somente para https://github.com/laurorual/MustardOS-R36S-port/issues.

English: [install.md](install.md).

## O que você precisa

- Um R36S ou R35S com a tela **Panel 0** (placa R36S V12, device tree
  "R36S-V12 2023-08-18 Panel 0"). É o único aparelho testado. Outras
  telas e clones podem mostrar tela preta ou imagem embaralhada: nada
  estraga, basta voltar o cartão antigo.
- Um cartão microSD de 8 GB ou mais (de boa marca; o cartão do slot 1
  guarda o sistema e os seus saves).
- Um PC com leitor de cartão e balenaEtcher, Rufus ou Raspberry Pi Imager.
- Opcional: um adaptador Wi-Fi USB com chip **Realtek RTL8821CU** (para
  SFTP, hora automática e atualizações); um segundo microSD (FAT32 ou
  exFAT) para ROMs no slot 2.

Guarde o seu cartão original: gravar esta imagem apaga o cartão usado.

## Gravar o cartão

1. Na [página de releases](https://github.com/laurorual/MustardOS-R36S-port/releases)
   baixe `MustardOS-R36S-port-<versão>.img.xz` e
   `MustardOS-R36S-port-<versão>.img.xz.sha256`. Conferência opcional no
   Linux/macOS: `sha256sum -c MustardOS-R36S-port-<versão>.img.xz.sha256`.
2. Grave o arquivo `.img.xz` no cartão com balenaEtcher, Rufus ou
   Raspberry Pi Imager ("Use custom"); eles descompactam sozinhos. No
   Linux sem eles:
   `xz -dc MustardOS-R36S-port-<versão>.img.xz | sudo dd of=/dev/sdX bs=4M conv=fsync status=progress`
   (sdX = o cartão; confira com `lsblk`).
3. Se o Windows oferecer "formatar" o cartão depois, responda **não**
   (as partições são do Linux).

## Primeira inicialização

1. Coloque o cartão no **slot 1** (o slot de onde o aparelho inicia; na
   maioria marcado TF1/INT) e ligue. O logo mostra "MustardOS R36S /
   R35S, unofficial port" e depois abre a configuração inicial do
   MustardOS.
2. Ajuste **Data e hora** e **Idioma** (Português (BR)); **Perfis** e
   **Teste de botões** (confere cada botão) são opcionais. **Desligar**
   desliga sem instalar: a configuração inicial abre de novo no próximo
   início.
3. **Instalar** pergunta como formatar o armazenamento do cartão (jogos,
   saves, configurações):
   - **exFAT** (recomendado): Windows, macOS e Linux leem e gravam, então
     os jogos vão direto para as pastas `ROMS` do cartão.
   - **FAT32**: todo computador lê, mas nenhum arquivo passa de 4 GB.
   - **EXT4**: aguenta melhor uma queda de energia, mas o Windows não lê
     sem programas extras.

   O aparelho reinicia, o armazenamento cresce até ocupar o cartão inteiro
   e é formatado (alguns segundos), e aparece o menu do MustardOS com a
   data, o idioma e o perfil escolhidos.

   > **exFAT, FAT32 e queda de energia:** configurações, saves e a área de
   > atualização do sistema ficam nesse mesmo armazenamento. Esses
   > sistemas de arquivos não têm journal: se a bateria acabar ou o
   > console for desligado durante uma gravação (salvar o jogo, mudar uma
   > configuração, instalar uma atualização), arquivos podem se corromper
   > e, no pior caso, o cartão precisa ser gravado de novo. Desligue pelo
   > menu, mantenha a bateria carregada e faça cópia dos saves.
4. Wi-Fi (com o adaptador): Configuração → Conectividade → Rede Wi-Fi.

## Jogos e BIOS

Nenhum jogo ou BIOS acompanha o sistema; use apenas cópias de jogos que
você possui.

- **No PC (exFAT ou FAT32):** desligue o aparelho, coloque o cartão no
  leitor do PC e copie os jogos para `ROMS/<sistema>` e as BIOS para
  `MUOS/bios` na unidade de armazenamento (a grande; não mexa na unidade
  pequena de boot). Ejete o cartão antes de tirá-lo.
- **Pelo Wi-Fi (SFTP):** Configuração → Conectividade → Serviços web →
  Arquivos via SFTP → ligado. Conecte com FileZilla ou WinSCP: SFTP, o IP
  do aparelho, porta **2022**, usuário **muos**, senha **muos**. Jogos em
  `ROMS/<sistema>`, BIOS em `MUOS/bios`.
- **Num segundo cartão (slot 2):** cartão FAT32/exFAT com a pasta `ROMS`
  (`ROMS/<sistema>`); o MustardOS o mostra como SD2 em Explorar conteúdo.

Sistemas que precisam de BIOS: PlayStation (`scph5501.bin` ou similar),
Sega CD (`bios_CD_U.bin`…), PC Engine CD (`syscard3.pce`), Dreamcast
(`dc/dc_boot.bin`, `dc/dc_flash.bin`), Saturn (`saturn_bios.bin`).

## Atualizações

Só a partição do sistema muda; jogos, saves e configurações ficam. Nada
é baixado sem perguntar.

- Com Wi-Fi: Aplicativos → Ferramentas de sistema → "Buscar atualização
  online" mostra uma versão nova e pergunta antes de baixar e antes de
  instalar.
- Sem Wi-Fi: copie `MustardOS-R36S-port-<versão>.p2.img.gz` e o
  `.p2.img.sha256` da release para `MUOS/update` no cartão (no PC com um
  cartão exFAT/FAT32, ou por SFTP) e use Aplicativos → Ferramentas de
  sistema → "Instalar atualização do sistema".
- A atualização mostra o progresso, reinicia o aparelho duas vezes e leva
  cerca de 10 minutos: deixe ligado, no carregador ou com pelo menos 30 %
  de bateria. Se o sistema novo não chegar ao menu, a inicialização
  seguinte volta sozinha ao anterior; um kernel novo só fica depois de
  chegar ao menu.
- Regravar o cartão inteiro (passos acima) apaga os saves: copie antes
  `MUOS/save` e `MUOS/pickles`.

## Bom saber

- Sistemas pesados (PSP, Dreamcast, Saturn, N64) rodam melhor na bateria:
  o carregador esquenta o processador e ele reduz a velocidade.
- Configuração → Configurações perigosas → Undervolt reduz o calor; se
  algum jogo travar com ele ligado, desligue no mesmo lugar.
- Problemas conhecidos: [known-issues.md](known-issues.md).
- Senha de root (SSH, desligado por padrão): `root`. Troque-a se ligar o
  SSH.
