vamos adaptar para o stremlit



me diga o que baixar no vscode





import tkinter as tk

from tkinter import messagebox, scrolledtext

import random

import requests

import json

import os

import webbrowser

import urllib.parse

from collections import Counter



# Tenta importar o Pillow para o logo

try:

    from PIL import Image, ImageTk

    PILLOW_INSTALADO = True

except ImportError:

    PILLOW_INSTALADO = False



# Configurações de Design e Arquivos

ROXO_LOTO = "#4b0082" 

BRANCO = "#ffffff"

PRETO = "#000000"

CINZA_CLARO = "#f0f0f0"

ARQUIVO_CACHE = "loto_completo_cache.json"

ARQUIVO_PALPITES = "meus_palpites.json"

CAMINHO_LOGO = "logo.png"



class LotofacilApp:

    def __init__(self, root):

        self.root = root

        self.root.title("Lotomind")

        # --- INSERIR A LINHA ABAIXO PARA O ÍCONE ---

        try:

            self.root.iconbitmap("logo.ico")

        except:

            pass # Caso o arquivo não seja encontrado, o app abre com o ícone padrão

        # ------------------------------------------

        self.root.geometry("400x800")

        self.root.configure(bg=BRANCO)

        

        self.historico_sorteios = []

        self.ultimo_resultado = None

        self.palpite_atual = None 

        

        # Carrega palpites do JSON ao iniciar

        self.palpites_salvos = self.carregar_palpites_json()



        self.container = tk.Frame(self.root, bg=BRANCO)

        self.container.pack(expand=True, fill="both")



        self.show_welcome_screen()



    def carregar_palpites_json(self):

        if os.path.exists(ARQUIVO_PALPITES):

            try:

                with open(ARQUIVO_PALPITES, "r") as f:

                    return json.load(f)

            except:

                return []

        return []



    def salvar_no_json(self):

        try:

            with open(ARQUIVO_PALPITES, "w") as f:

                json.dump(self.palpites_salvos, f, indent=4)

        except Exception as e:

            messagebox.showerror("Erro", f"Não foi possível salvar no arquivo: {e}")



    def clear_screen(self):

        for widget in self.container.winfo_children():

            widget.destroy()



    # --- TELAS ---

    def show_welcome_screen(self):

        self.clear_screen()

        main_frame = tk.Frame(self.container, bg=BRANCO)

        main_frame.place(relx=0.5, rely=0.45, anchor="center")



        carregou_imagem = False

        if PILLOW_INSTALADO and os.path.exists(CAMINHO_LOGO):

            try:

                img = Image.open(CAMINHO_LOGO)

                img = img.resize((400, 400), Image.LANCZOS)

                self.logo_img = ImageTk.PhotoImage(img)

                lbl_logo = tk.Label(main_frame, image=self.logo_img, bg=BRANCO)

                lbl_logo.pack(pady=10)

                carregou_imagem = True

            except: pass



        if not carregou_imagem:

            tk.Label(main_frame, text="LOTOFÁCIL\nMASTER", font=("Arial", 35, "bold"), 

                     bg=BRANCO, fg=ROXO_LOTO).pack(pady=60)



        tk.Button(main_frame, text="ENTRAR", bg=ROXO_LOTO, fg=BRANCO, 

                  font=("Arial", 14, "bold"), width=15, height=2,

                  command=self.iniciar_app).pack(pady=20)

        

        # Crédito discreto no rodapé da tela de entrada

        tk.Label(self.container, text="Developed by Rodrigo Carielo", font=("Arial", 7, "italic"), 

                 bg=BRANCO, fg="#888888").pack(side="bottom", pady=5)



    def iniciar_app(self):

        self.buscar_dados_completos()

        self.show_main_screen()



    def buscar_dados_completos(self):

        if os.path.exists(ARQUIVO_CACHE):

            try:

                with open(ARQUIVO_CACHE, "r") as f:

                    data = json.load(f)

                    self.historico_sorteios = data

                    if data: self.ultimo_resultado = data[0]

            except: pass

        try:

            r = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/", timeout=7)

            if r.status_code == 200:

                self.historico_sorteios = r.json()[:60]

                self.ultimo_resultado = self.historico_sorteios[0]

                with open(ARQUIVO_CACHE, "w") as f:

                    json.dump(self.historico_sorteios, f)

        except:

            if not self.historico_sorteios:

                messagebox.showwarning("Conexão", "Sem internet. Usando dados salvos.")



    def forcar_atualizacao(self):

        try:

            r = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/", timeout=7)

            if r.status_code == 200:

                self.historico_sorteios = r.json()[:60]

                self.ultimo_resultado = self.historico_sorteios[0]

                with open(ARQUIVO_CACHE, "w") as f:

                    json.dump(self.historico_sorteios, f)

                messagebox.showinfo("Sucesso", "Dados atualizados com sucesso!")

                self.show_main_screen()

        except:

            messagebox.showerror("Erro", "Falha ao conectar com o servidor para atualizar.")



    def compartilhar_palpite_atual(self):

        if not self.palpite_atual:

            messagebox.showinfo("Aviso", "Gere um jogo primeiro para compartilhar!")

            return

        

        nums_str = " ".join([str(n).zfill(2) for n in self.palpite_atual])

        concurso = self.ultimo_resultado.get('proximoConcurso', '---')

        texto = f"🍀 Sugestão Lotomind\nPara o Concurso: {concurso}\nNúmeros: {nums_str}"

        

        webbrowser.open(f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}")



    def show_main_screen(self):

        self.clear_screen()

        

        # Botão pequeno de forçar atualização no topo

        tk.Button(self.container, text="forçar atualizar jogo", font=("Arial", 7), bg=CINZA_CLARO, 

                  command=self.forcar_atualizacao).pack(pady=2, anchor="ne", padx=10)



        tk.Label(self.container, text="LOTOFÁCIL MASTER", font=("Arial", 18, "bold"), bg=BRANCO, fg=ROXO_LOTO).pack(pady=(5, 5))

        

        if self.ultimo_resultado:

            frame_proximo = tk.Frame(self.container, bg=CINZA_CLARO)

            frame_proximo.pack(fill="x", padx=20, pady=5)

            

            prox_num = self.ultimo_resultado.get('proximoConcurso', '---')

            prox_data = self.ultimo_resultado.get('dataProximoSorteio', '---')

            prox_premio = self.ultimo_resultado.get('valorEstimadoProximoConcurso', 0)

            

            if isinstance(prox_premio, (int, float)):

                prox_premio = f"R$ {prox_premio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



            tk.Label(frame_proximo, text=f"PRÓXIMO CONCURSO: {prox_num}", font=("Arial", 8, "bold"), bg=CINZA_CLARO).pack(pady=2)

            tk.Label(frame_proximo, text=f"DATA: {prox_data} | PRÊMIO: {prox_premio}", font=("Arial", 9, "bold"), bg=CINZA_CLARO, fg=ROXO_LOTO).pack(pady=2)



        tk.Label(self.container, text="SUGESTÃO DE JOGO", font=("Arial", 10, "bold"), bg=BRANCO).pack(pady=(10, 5))

        

        self.label_jogo = tk.Label(self.container, text="-- -- -- -- --\n-- -- -- -- --\n-- -- -- -- --", 

                                   font=("Courier", 16, "bold"), bg=CINZA_CLARO, fg=ROXO_LOTO, 

                                   width=20, height=4, relief="solid", bd=1)

        self.label_jogo.pack()



        # Botões de Ação Imediata

        frame_btn = tk.Frame(self.container, bg=BRANCO)

        frame_btn.pack(pady=10)



        tk.Button(frame_btn, text="GERAR", bg=ROXO_LOTO, fg=BRANCO, font=("Arial", 10, "bold"), width=10, command=self.gerar_jogo).grid(row=0, column=0, padx=5)

        tk.Button(frame_btn, text="SALVAR", bg="#28a745", fg=BRANCO, font=("Arial", 10, "bold"), width=10, command=self.salvar_palpite_acao).grid(row=0, column=1, padx=5)



        # Opção de compartilhar WhatsApp para o jogo gerado

        tk.Button(self.container, text="COMPARTILHAR JOGO (WhatsApp)", bg="#25D366", fg=BRANCO, 

                  font=("Arial", 9, "bold"), width=25, command=self.compartilhar_palpite_atual).pack(pady=5)



        style_m = {"font": ("Arial", 10, "bold"), "width": 25, "height": 2, "bg": CINZA_CLARO}

        

        tk.Button(self.container, text="VER ÚLTIMO RESULTADO", command=self.exibir_resultado_na_tela, **style_m).pack(pady=5)

        tk.Button(self.container, text="MEUS PALPITES (JSON)", command=self.show_saved_palpites, **style_m).pack(pady=5)

        tk.Button(self.container, text="ESTATÍSTICAS", command=self.show_stats_menu, **style_m).pack(pady=5)

        

        self.frame_res = tk.Frame(self.container, bg=BRANCO)

        self.frame_res.pack(pady=10)



        # Rodapé com o autor de forma discreta

        tk.Label(self.container, text="Developed by Rodrigo Carielo", font=("Arial", 7, "italic"), 

                  bg=BRANCO, fg="#888888").pack(side="bottom", pady=2)



        tk.Button(self.container, text="SAIR DO APP", font=("Arial", 8, "bold"), bg=BRANCO, fg="#aa0000", bd=0, 

                  command=self.root.destroy).pack(side="bottom", pady=5)



    def exibir_resultado_na_tela(self):

        for w in self.frame_res.winfo_children(): w.destroy()

        if not self.ultimo_resultado: return

        

        res = self.ultimo_resultado

        nums = res.get('dezenas') or res.get('listaDezenas')

        

        tk.Label(self.frame_res, text=f"Resultado Concurso {res['concurso']}:", 

                  font=("Arial", 9, "bold"), bg=BRANCO, fg=PRETO).pack()

        tk.Label(self.frame_res, text=self.formatar_numeros(nums), 

                  font=("Courier", 11, "bold"), bg=BRANCO, fg=ROXO_LOTO).pack()



    def salvar_palpite_acao(self):

        if not self.palpite_atual:

            messagebox.showinfo("Aviso", "Gere um jogo primeiro!")

            return

        

        concurso = self.ultimo_resultado.get('proximoConcurso', '---')

        data_sorteio = self.ultimo_resultado.get('dataProximoSorteio', '---')

        

        novo_palpite = {

            "concurso": concurso,

            "data": data_sorteio,

            "numeros": self.palpite_atual

        }

        

        self.palpites_salvos.append(novo_palpite)

        self.salvar_no_json()

        messagebox.showinfo("Sucesso", f"Palpite para o concurso {concurso} salvo!")



    def show_saved_palpites(self):

        self.clear_screen()

        tk.Label(self.container, text="PALPITES SALVOS (JSON)", font=("Arial", 14, "bold"), bg=BRANCO, fg=ROXO_LOTO).pack(pady=15)

        

        if not self.palpites_salvos:

            tk.Label(self.container, text="Nenhum palpite no arquivo.", bg=BRANCO).pack(pady=20)

        else:

            tk.Label(self.container, text="HISTÓRICO DOS PALPITES", font=("Arial", 10, "bold"), bg=CINZA_CLARO, fg=PRETO).pack(fill="x")

            

            txt_area = scrolledtext.ScrolledText(self.container, width=42, height=15, font=("Courier", 9, "bold"))

            txt_area.pack(pady=10, padx=10)

            

            for p in reversed(self.palpites_salvos):

                nums_str = " ".join([str(n).zfill(2) for n in p['numeros']])

                

                acertos_info = "Aguardando Sorteio..."

                for sorteio in self.historico_sorteios:

                    if str(sorteio['concurso']) == str(p['concurso']):

                        dezenas_sorteadas = [int(x) for x in (sorteio.get('dezenas') or sorteio.get('listaDezenas'))]

                        acertos = len(set(p['numeros']) & set(dezenas_sorteadas))

                        acertos_info = f"ACERTOS: {acertos} PONTOS"

                        break

                

                txt_area.insert(tk.END, f"CONCURSO: {p['concurso']} | {acertos_info}\n")

                txt_area.insert(tk.END, f"{nums_str}\n{'-'*38}\n")

            

            txt_area.config(state='disabled')



            tk.Button(self.container, text="ESTATÍSTICAS DOS PALPITES", bg=ROXO_LOTO, fg=BRANCO, 

                      font=("Arial", 10, "bold"), width=30, command=self.calcular_estatisticas_palpites).pack(pady=5)



            tk.Button(self.container, text="ENVIAR TUDO P/ WHATSAPP", bg="#25D366", fg=BRANCO, 

                      font=("Arial", 10, "bold"), width=30, command=self.compartilhar_whatsapp).pack(pady=5)



            tk.Button(self.container, text="LIMPAR HISTÓRICO", bg="#dc3545", fg=BRANCO, 

                      font=("Arial", 8), width=20, command=self.limpar_historico).pack(pady=5)



        tk.Button(self.container, text="VOLTAR", bg=PRETO, fg=BRANCO, width=15, command=self.show_main_screen).pack(pady=15)



    def calcular_estatisticas_palpites(self):

        if not self.palpites_salvos:

            messagebox.showinfo("Estatísticas", "Nenhum palpite para analisar.")

            return



        lista_acertos = []

        contagem_faixas = {i: 0 for i in range(16)} 

        

        for p in self.palpites_salvos:

            for sorteio in self.historico_sorteios:

                if str(sorteio['concurso']) == str(p['concurso']):

                    dezenas_sorteadas = [int(x) for x in (sorteio.get('dezenas') or sorteio.get('listaDezenas'))]

                    acertos = len(set(p['numeros']) & set(dezenas_sorteadas))

                    lista_acertos.append(acertos)

                    contagem_faixas[acertos] += 1

                    break



        if not lista_acertos:

            messagebox.showinfo("Estatísticas", "Os concursos dos seus palpites ainda não ocorreram ou não estão no cache.")

            return



        media = sum(lista_acertos) / len(lista_acertos)

        minimo = min(lista_acertos)

        maximo = max(lista_acertos)

        total_p = len(lista_acertos)

        

        abaixo_9 = sum(contagem_faixas[i] for i in range(10))



        relatorio = f"ESTATÍSTICAS DOS SEUS JOGOS\n"

        relatorio += f"Total analisado: {total_p} jogos\n"

        relatorio += f"{'='*30}\n"

        relatorio += f"Média de acertos: {media:.2f}\n"

        relatorio += f"Mínimo de acertos: {minimo}\n"

        relatorio += f"Máximo de acertos: {maximo}\n"

        relatorio += f"{'='*30}\n"

        relatorio += f"15 ACERTOS: {contagem_faixas[15]}\n"

        relatorio += f"14 ACERTOS: {contagem_faixas[14]}\n"

        relatorio += f"13 ACERTOS: {contagem_faixas[13]}\n"

        relatorio += f"12 ACERTOS: {contagem_faixas[12]}\n"

        relatorio += f"11 ACERTOS: {contagem_faixas[11]}\n"

        relatorio += f"10 ACERTOS: {contagem_faixas[10]}\n"

        relatorio += f"9 OU MENOS: {abaixo_9}\n"



        self.show_text_report("DESEMPENHO DOS PALPITES", relatorio)



    def limpar_historico(self):

        if messagebox.askyesno("Confirmar", "Deseja apagar todos os palpites?"):

            self.palpites_salvos = []

            self.salvar_no_json()

            self.show_saved_palpites()



    def compartilhar_whatsapp(self):

        if not self.palpites_salvos: return

        texto = "📊 Meus Palpites Lotofácil Master\n\n"

        for p in self.palpites_salvos[-5:]:

            nums_str = " ".join([str(n).zfill(2) for n in p['numeros']])

            texto += f"🍀 Conc: {p['concurso']}\n`{nums_str}`\n\n"

        

        webbrowser.open(f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}")

    def gerar_jogo(self):

        if not self.ultimo_resultado or not self.historico_sorteios: return

        

        ult_60 = self.historico_sorteios[:60]

        ult_5 = self.historico_sorteios[:5]

        dezenas_ultimo = [int(n) for n in (self.ultimo_resultado.get('dezenas') or self.ultimo_resultado.get('listaDezenas'))]

        

        contagem = Counter()

        for s in ult_60:

            contagem.update([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])

        

        top_10 = [n for n, c in contagem.most_common(10)]

        bottom_6 = [n for n, c in contagem.most_common()[-6:]]

        

        excluir_flow = []

        for n in range(1, 26):

            count_seq = 0

            for s in ult_5:

                res_sorteio = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]

                if n in res_sorteio: count_seq += 1

                else: break 

            if count_seq >= 4: excluir_flow.append(n)

        

        obrigatorios_atraso = []

        ult_3 = self.historico_sorteios[:3]

        for n in range(1, 26):

            saiu_nos_3 = False

            for s in ult_3:

                res_sorteio = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]

                if n in res_sorteio: 

                    saiu_nos_3 = True

                    break

            if not saiu_nos_3: 

                obrigatorios_atraso.append(n)



        tentativas = 0

        while tentativas < 5000:

            tentativas += 1

            jogo = sorted(random.sample(range(1, 26), 15))

            

            # --- REGRAS IMUTÁVEIS ---

            r_count = len([n for n in jogo if n in dezenas_ultimo])

            if r_count not in [8, 9]: continue

            

            pares = len([n for n in jogo if n % 2 == 0])

            impares = 15 - pares

            if not ((impares == 8 and pares == 7) or (impares == 7 and pares == 8)): continue

            

            if not all(n in jogo for n in obrigatorios_atraso): continue



            # --- REGRAS FLEXÍVEIS ---

            t_ok = 5 <= len([n for n in jogo if n in top_10]) <= 7

            b_ok = 3 <= len([n for n in jogo if n in bottom_6]) <= 4

            f_ok = not any(n in jogo for n in excluir_flow)

            

            # Cálculo de Confiança (Imutáveis já são 100%, calculamos as flexíveis)

            regras_extras = [t_ok, b_ok, f_ok]

            acertos_regras = regras_extras.count(True)

            

            # Se atingir 100% das flexíveis ou estourar o limite de tentativas

            if acertos_regras == 3 or tentativas > 4500:

                confianca = 100 if acertos_regras == 3 else int(70 + (acertos_regras * 10))

                

                motivos = []

                if not t_ok: motivos.append("Top10 fora")

                if not b_ok: motivos.append("Bottom6 fora")

                if not f_ok: motivos.append("Números em Flow")

txt_motivo = "Todas as métricas atendidas!" if not motivos else f"Ajuste: {', '.join(motivos)}"

                

                self.palpite_atual = jogo

                self.label_jogo.config(text=self.formatar_numeros(jogo))

                messagebox.showinfo("Sugestão Gerada", f"Confiança: {confianca}%\n\n{txt_motivo}")

                return



        self.palpite_atual = jogo

        self.label_jogo.config(text=self.formatar_numeros(jogo))



    def formatar_numeros(self, lista):

        l = [str(n).zfill(2) for n in lista]

        return f"{' '.join(l[:5])}\n{' '.join(l[5:10])}\n{' '.join(l[10:15])}"



    def show_stats_menu(self):

        self.clear_screen()

        tk.Label(self.container, text="ESTATÍSTICAS", font=("Arial", 16, "bold"), bg=BRANCO, fg=ROXO_LOTO).pack(pady=20)

        tk.Button(self.container, text="RANKING GERAL (60 JOGOS)", bg=CINZA_CLARO, width=30, height=2, command=self.stats_ranking).pack(pady=5)

        tk.Button(self.container, text="VOLTAR", bg=PRETO, fg=BRANCO, width=20, command=self.show_main_screen).pack(pady=20)



    def stats_ranking(self):

        if not self.historico_sorteios: return

        ult_60 = self.historico_sorteios[:60]

        ult_5 = self.historico_sorteios[:5]

        contagem = Counter()

        for s in ult_60:

            contagem.update([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])

        

        top_10 = contagem.most_common(10)

        bottom_6 = contagem.most_common()[-6:]

        

             

        tardy, flow = [], []

        for n in range(1, 26):

            count_5, last_seen = 0, -1

            for i, s in enumerate(ult_5):

                res = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]

                if n in res:

                    count_5 += 1

                    if last_seen == -1: last_seen = i

            if count_5 >= 4: flow.append(f"{n:02d}({count_5}x)")

            if last_seen > 0 or last_seen == -1:

                atraso = last_seen if last_seen != -1 else 5

                if atraso >= 3: tardy.append(f"{n:02d}({atraso}j)")



        report = f"RANKING ÚLTIMOS 60 SORTEIOS\n"

        report += "="*30 + "\nTOP 10 MAIS SORTEADOS:\n"

        for n, c in top_10: report += f" Dezena {n:02d} | {c} vezes\n"

        report += "\nBOTTOM 6 MENOS SORTEADOS:\n"

        for n, c in bottom_6: report += f" Dezena {n:02d} | {c} vezes\n"

        report += "\nTARDY: " + ", ".join(tardy)

        report += "\nFLOW: " + ", ".join(flow)

        self.show_text_report("ESTATÍSTICAS AVANÇADAS", report)



    def show_text_report(self, titulo, conteudo):

        self.clear_screen()

        tk.Label(self.container, text=titulo, font=("Arial", 14, "bold"), bg=BRANCO, fg=ROXO_LOTO).pack(pady=10)

        txt = scrolledtext.ScrolledText(self.container, width=40, height=25, font=("Courier", 10))

        txt.insert(tk.INSERT, conteudo)

        txt.config(state='disabled')

        txt.pack(pady=10)

        tk.Button(self.container, text="VOLTAR", bg=ROXO_LOTO, fg=BRANCO, width=20, command=self.show_main_screen).pack(pady=10)



if __name__ == "__main__":

    root = tk.Tk()

    app = LotofacilApp(root)

    root.mainloop()