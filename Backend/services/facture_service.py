from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from Backend import models, schemas
import io, csv


def generate_invoice(db: Session, payload: schemas.FactureGenerationRequest):
    """
    Invoice Generation Pipeline:
    Aggregates unbilled delivery records, applies pricing rules,
    performs currency conversion, and creates a finalized invoice entity.
    """
    client_id = payload.id_client
    month = payload.mois
    year = payload.annee

    # 1. Retrieve unbilled delivery records within period
    deliveries = (
        db.query(models.BonsDeLivraison)
        .outerjoin(models.FactureBonLivraison)
        .filter(
            models.BonsDeLivraison.id_client == client_id,
            models.FactureBonLivraison.id_facture == None
        ).all()
    )

    if not deliveries:
        raise HTTPException(status_code=400, detail="No billable records found for this period.")

    # 2. Retrieve currency rate configuration
    rate = db.query(models.TauxDeChangeMensuel).filter_by(
        mois=month, annee=year
    ).first()
    if not rate:
        raise HTTPException(status_code=400, detail="Missing currency rate configuration.")

    conversion_rate = Decimal(str(rate.taux))

    # 3. Aggregate line items
    delivery_ids = [d.id_bl for d in deliveries]
    lines = (
        db.query(models.LigneBL)
        .options(joinedload(models.LigneBL.article))
        .filter(models.LigneBL.id_bl.in_(delivery_ids))
        .all()
    )

    # 4. Financial Computation (Confidential Business Logic)
    subtotal_eur = Decimal('0.00')
    for line in lines:
        # [REDACTED]: proprietary pricing, discount, and rounding logic
        subtotal_eur += Decimal(str(line.prix_total_ligne))

    # [REDACTED]: global discount and net calculation rules
    net_eur = subtotal_eur
    net_dt = (net_eur * conversion_rate)

    # 5. Create invoice entity
    invoice = models.Factures(
        numero_facture=payload.numero_facture_manuel,
        date_facture=date(year, month, 1),
        id_client=client_id,
        montant_total_euro=subtotal_eur,
        montant_net_euro=net_eur,
        montant_net_dt=net_dt,
        taux_conversion=conversion_rate,
        incoterm=payload.incoterm
    )

    db.add(invoice)
    db.flush()

    # 6. Link deliveries to invoice
    for d in deliveries:
        db.add(models.FactureBonLivraison(id_facture=invoice.id_facture, id_bl=d.id_bl))

    db.commit()
    db.refresh(invoice)
    return invoice


def export_invoice_csv(invoice, lines):
    """
    CSV Export Pattern:
    Produces a structured financial export suitable for accounting integration.
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')

    writer.writerow(["INVOICE", invoice.numero_facture])
    writer.writerow(["DATE", invoice.date_facture.strftime("%d/%m/%Y")])
    writer.writerow(["CLIENT", invoice.client.nom_client])
    writer.writerow([])

    writer.writerow([
        "Reference", "Description", "Quantity",
        "Unit Price", "Line Total EUR", "Line Total Local"
    ])

    for line in lines:
        # [REDACTED]: archived pricing and category logic
        writer.writerow([
            line.article.reference if line.article else "N/A",
            "CONFIDENTIAL",
            int(line.quantite),
            float(line.prix_unitaire),
            float(line.prix_total_ligne),
            float(line.prix_total_ligne)  # placeholder conversion
        ])

    content = output.getvalue()
    return io.BytesIO(content.encode("utf-8"))


def update_exchange_rate(db: Session, month: int, year: int, new_rate: Decimal):
    """
    Configuration Update Pattern:
    Updates monthly currency conversion settings used in financial computations.
    """
    rate = db.query(models.TauxDeChangeMensuel).filter_by(
        mois=month, annee=year
    ).first()

    if not rate:
        raise HTTPException(status_code=404, detail="Exchange rate configuration not found.")

    rate.taux = new_rate
    db.commit()
    return {"status": "updated"}


def get_clients_with_pending_deliveries(db: Session, month: int, year: int):
    """
    Pending Billing Detection:
    Identifies clients with unbilled delivery records for a given period.
    """
    billed_subquery = db.query(models.FactureBonLivraison.id_bl)

    clients = (
        db.query(models.Clients)
        .join(models.BonsDeLivraison)
        .filter(~models.BonsDeLivraison.id_bl.in_(billed_subquery))
        .distinct()
        .all()
    )

    return clients