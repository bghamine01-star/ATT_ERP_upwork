import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from sqlalchemy.orm import Session
from Backend import models

PAGE_HEIGHT = 841.89

def generer_facture_pdf(db: Session, facture_id: int):
    facture = db.query(models.Factures).filter(models.Factures.id_facture == facture_id).first()
    if not facture: return None

    articles = []
    for assoc in facture.bons_livraison_associes:
        for ligne in assoc.bon_livraison.lignes:
            articles.append(ligne)

    y_start_articles = 265.617
    line_spacing = 14
    nb_total = len(articles)

# --- ÉTAPE A : SIMULATION SYNCHRONISÉE ---
    temp_idx = 0
    total_pages = 0
    sim_final_done = False

    while temp_idx < nb_total or not sim_final_done:
        total_pages += 1
        
        restants = articles[temp_idx:]
        espace_requis = len(restants) * line_spacing
        
        # Si on peut mettre les articles restants + le bloc final sur cette page
        if temp_idx < nb_total and (y_start_articles + espace_requis) <= 665.0:
            temp_idx = nb_total # Tous les articles sont placés
            sim_final_done = True
        elif temp_idx >= nb_total:
            # Plus d'articles, mais on doit quand même compter la page finale
            sim_final_done = True
        else:
            # Trop d'articles, cette page sera une page INTERMÉDIAIRE
            # On simule le remplissage de la page jusqu'à 770.0
            nb_ajoute = 0
            curr_y = y_start_articles
            while temp_idx < nb_total and (curr_y + line_spacing) <= 770.0:
                curr_y += line_spacing
                temp_idx += 1
                nb_ajoute += 1
            if nb_ajoute == 0: # Sécurité
                temp_idx = nb_total
                sim_final_done = True

    # --- ÉTAPE B : GÉNÉRATION RÉELLE ---
    output = PdfWriter()
    PATH_INTERMEDIAIRE = "Backend/static/amine_intermediaire.pdf"
    PATH_FINAL = "Backend/static/amine.pdf"
    
    index_article = 0
    page_num = 1
    final_page_done = False

    while index_article < nb_total or not final_page_done:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        articles_restants = articles[index_article:]
        espace_requis = len(articles_restants) * line_spacing
        
        # Choix du template
        if index_article < nb_total and (y_start_articles + espace_requis) <= 665.0:
            est_finale = True
            current_template = PATH_FINAL
            y_limite_page = 665.0
            final_page_done = True
        elif index_article >= nb_total:
            # On génère une page finale vide d'articles (juste les totaux)
            est_finale = True
            current_template = PATH_FINAL
            y_limite_page = 665.0
            final_page_done = True
        else:
            est_finale = False
            current_template = PATH_INTERMEDIAIRE
            y_limite_page = 770.0

        # --- FONCTION WRITE ---
        def write(x, y_inkscape, text, bold=False, size=10, align="left"):
            font_name = "Times-Bold" if bold else "Times-Roman"
            can.setFont(font_name, size)
            y_real = PAGE_HEIGHT - y_inkscape
            if align == "center": can.drawCentredString(x, y_real, str(text))
            elif align == "right": can.drawRightString(x, y_real, str(text))
            else: can.drawString(x, y_real, str(text))

        # --- BLOCS COMMUNS (En-tête) ---
        write(428.605, 70.707, f"Facture N° {facture.numero_facture}", bold=True, size=12)
        write(434.629, 93.328, f"Date: {facture.date_facture.strftime('%d/%m/%Y')}", bold=True, size=11)
        client = facture.client
        write(21.023, 166.383, f"Client : {client.code_client} / {client.nom_client}", bold=True)
        write(20.637, 181.426, f"Adresse : {client.adresse}")
        write(20.742, 196.867, f"M.F : {client.matricule_fiscal or 'N/A'}")
        list_bls = [assoc.bon_livraison.numero_bl for assoc in facture.bons_livraison_associes]
        write(20.742, 211.906, f"Bls N° : {', '.join(list_bls)}")

        # --- BOUCLE ARTICLES ---
        current_y = y_start_articles
        articles_sur_cette_page = 0
        while index_article < nb_total and (current_y + line_spacing) <= y_limite_page:
            ligne = articles[index_article]
            #nom_art = getattr(ligne, 'nom_article_archive', None) or ligne.article.nom_article
            # Dans votre boucle PDF
            cat_art = getattr(ligne, 'categorie_archive', None) or (ligne.article.categorie if ligne.article else "N/A")
            remise_art = float(ligne.remise or 0)
            brut_ligne = float(ligne.prix_total_ligne)
            net_ligne_euro = brut_ligne * (1 - (remise_art / 100))
            tot_dt = net_ligne_euro * float(facture.taux_conversion)

            write(20.700, current_y, ligne.article.reference or "")
            write(108, current_y, f"{cat_art[:40]}")
            write(275, current_y, ligne.stock_se.numero_se if ligne.stock_se else "", align="center")
            write(347, current_y, ligne.quantite, align="center")
            write(409, current_y, f"{float(ligne.prix_unitaire):.2f}", align="center")
            write(472, current_y, f"{net_ligne_euro:.2f}", align="center")
            write(536, current_y, f"{tot_dt:.3f}", align="center")

            current_y += line_spacing
            index_article += 1
            articles_sur_cette_page += 1

        # --- BLOC FINAL ---
        if est_finale:
            write(20.500, 699, f"INCOTERM:{facture.incoterm or 'FOB'}", bold=True)
            write(325.336, 699, f"POIDS NET : {facture.poid_en_kg or 0} KG", bold=True)
            write(535, 699, f"{float(facture.montant_total_euro):.2f}", bold=True, align="center")
            write(535, 713.5, f"{facture.remise_pourcentage}%", bold=True, align="center")
            write(535, 728.5, f"{float(facture.montant_net_euro):.2f}", bold=True, align="center")
            write(535, 742.5, f"{float(facture.taux_conversion):.3f}", bold=True, align="center")
            write(535, 756.5, f"{float(facture.montant_net_dt):.3f}", bold=True, align="center")

            to = can.beginText(30, PAGE_HEIGHT - 730)
            to.setFont("Times-Roman", 10)
            to.textLine(f" {facture.total_en_lettre_euro.upper()} Soit")
            to.textLine(f" {facture.total_en_lettre_dt.upper()}")
            can.drawText(to)

        write(297, 808.109, f"Page {page_num} de {total_pages}", align="center")
        can.save()
        packet.seek(0)

        # Fusion
        reader_template = PdfReader(open(current_template, "rb"))
        page_template = reader_template.pages[0]
        page_template.merge_page(PdfReader(packet).pages[0])
        output.add_page(page_template)
        
        page_num += 1
        # Sécurité ultime : éviter boucle infinie si espace template est trop petit
        if articles_sur_cette_page == 0 and not est_finale:
            break

    final_buffer = io.BytesIO()
    output.write(final_buffer)
    return final_buffer.getvalue()
  