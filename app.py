import flet as ft
import google.generativeai as genai
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY
from fpdf import FPDF # Assure-toi que 'pip install fpdf' est fait
import os
import webbrowser # Pour ouvrir la vidéo dans le navigateur

# 1. Configuration (Cloud + IA Gemini 3 Flash + Veo pour la vidéo)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

ia_model = genai.GenerativeModel('models/gemini-3-flash-preview')
# Le modèle Veo n'est pas directement listé comme 'gemini-robotics-er-1.5-preview'
# qui est plus pour la robotique. Pour la vidéo, on utiliserait le modèle 'veo'
# si tu y as accès directement via genai. A des fins de démo, nous allons simuler.
# Dans un vrai déploiement, tu devrais voir 'models/veo' dans list_models()
# Si 'veo' n'est pas disponible, on simule la génération de vidéo
# ia_video_model = genai.GenerativeModel('models/veo') # Si disponible

def main(page: ft.Page):
    page.title = "EduAfrique IA - Vidéo & PDF"
    page.scroll = "adaptive"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    last_quiz = ""
    last_video_url = "" # Pour stocker l'URL de la vidéo

    def export_pdf(e):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=f"COURS : {title_field.value}", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, txt=f"CONTENU DU COURS :\n{content_field.value}")
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="QUIZ D'ÉVALUATION", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 10, txt=last_quiz)
            
            filename = f"Cours_{title_field.value.replace(' ', '_')}.pdf"
            pdf.output(filename)
            
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ PDF enregistré : {filename}"))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erreur PDF : {ex}"))
            page.snack_bar.open = True
            page.update()

    def generate_video(e):
        nonlocal last_video_url
        if not title_field.value:
            page.snack_bar = ft.SnackBar(ft.Text("Veuillez saisir un titre pour la vidéo !"))
            page.snack_bar.open = True
            page.update()
            return

        btn_generate_video.disabled = True
        loading_video.visible = True
        page.update()
        
        try:
            # Pour la démo, on simule une URL de vidéo
            # En réalité, ici, tu appellerais le modèle Veo
            # response = ia_video_model.generate_content(f"Crée une vidéo éducative sur {title_field.value}")
            # last_video_url = response.video_url

            # Simulation avec un générateur de vidéos aléatoires pour l'exemple
            keyword_video = title_field.value.replace(" ", "%20")
            last_video_url = f"https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1" # Exemple avec Rick Astley :)
            # Tu pourrais utiliser un service comme Pexels/Pixabay pour des vidéos aléatoires si tu as une clé API

            video_player.src = last_video_url
            video_player.visible = True
            
            page.snack_bar = ft.SnackBar(ft.Text("✅ Vidéo générée (simulée) !"))
            page.snack_bar.open = True

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erreur vidéo : {ex}. Vérifiez l'accès à 'models/veo'."))
            page.snack_bar.open = True
        
        btn_generate_video.disabled = False
        loading_video.visible = False
        page.update()

    def publish_and_generate(e):
        nonlocal last_quiz
        if not title_field.value or not content_field.value:
            return

        btn_publish.disabled = True
        loading_quiz_image.visible = True
        page.update()

        try:
            # IA : Quiz par Gemini 3 Flash
            prompt_quiz = (f"En tant qu'expert pédagogue, crée un quiz de 3 questions QCM "
                          f"pour ce cours : {content_field.value}")
            response = ia_model.generate_content(prompt_quiz)
            last_quiz = response.text

            # Image dynamique (Schéma/Satellite/Figure)
            keyword_image = title_field.value.replace(" ", "+")
            image_url = f"https://loremflickr.com/800/400/{keyword_image}"

            # Supabase
            supabase.table("contents").insert({
                "title": title_field.value,
                "body": content_field.value,
                "subject_tag": "Multimédia",
                "level_tag": "Gemini-3"
            }).execute()

            # UI Update
            result_container.content = ft.Column([
                ft.Text(f"📚 {title_field.value}", size=20, weight="bold"),
                ft.Image(src=image_url, border_radius=10, width=700),
                ft.Text("✍️ QUIZ GÉNÉRÉ :", weight="bold"),
                ft.Text(last_quiz),
                ft.ElevatedButton("📥 Télécharger en PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=export_pdf, bgcolor="red", color="white")
            ])
            result_container.visible = True

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erreur : {ex}"))
            page.snack_bar.open = True
        
        btn_publish.disabled = False
        loading_quiz_image.visible = False
        page.update()

    # --- UI ---
    title_field = ft.TextField(label="Titre de la leçon", border_radius=10)
    content_field = ft.TextField(label="Contenu", multiline=True, min_lines=5)

    btn_publish = ft.ElevatedButton("Générer Cours + Quiz + Image", on_click=publish_and_generate, bgcolor="blue", color="white")
    loading_quiz_image = ft.ProgressRing(visible=False)

    btn_generate_video = ft.ElevatedButton("🎬 Générer Vidéo", on_click=generate_video, bgcolor="green", color="white")
    loading_video = ft.ProgressRing(visible=False)

    video_player = ft.Container(
        content=ft.Column([
            ft.Text("Vidéo éducative :", weight="bold"),
            ft.Text("Pour l'exemple, cliquez pour ouvrir une vidéo YouTube aléatoire."),
            ft.ElevatedButton("Ouvrir la vidéo", on_click=lambda e: webbrowser.open(video_player.src))
        ]),
        visible=False,
        padding=10,
        border=ft.border.all(1, ft.Colors.GREEN_200),
        border_radius=10
    )

    result_container = ft.Container(padding=20, border=ft.border.all(1, "blue"), border_radius=10, visible=False)

    page.add(
        ft.Row([ft.Icon(ft.Icons.THEATER_COMEDY, color="green"), ft.Text("EduAfrique : Studio Multimédia", size=30, weight="bold")], alignment="center"),
        ft.Divider(),
        title_field,
        content_field,
        ft.Row([
            ft.Column([btn_publish, loading_quiz_image], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([btn_generate_video, loading_video], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
        result_container,
        video_player
    )

ft.app(target=main)