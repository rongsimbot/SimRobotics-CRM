#!/usr/bin/env python3
"""SimRobotics CRM v2.1 - Excel-Integrated Military CRM"""
import os, sys, psycopg2, math, time
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get('CRM_SECRET', 'simrobotics-crm-2026')
app.config['TEMPLATES_AUTO_RELOAD'] = True

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'simrobotics_crm', 'user': 'sim_admin',
    'password': 'SimData_Vector_2026!', 'connect_timeout': 5
}

PAGE_SIZE = 25
ALLOWED_SORT_COLS = {
    'companies': ['name', 'sector', 'region', 'business_type', 'source_file'],
    'contacts': ['first_name', 'last_name', 'role', 'email', 'phone', 'source_file'],
    'military_bases': ['base_name', 'branch', 'state', 'city', 'command_name', 'contact_count', 'status', 'priority'],
    'military_contacts': ['contact_name', 'title', 'contact_role', 'email', 'phone'],
    'military_outreach': ['outreach_date', 'subject', 'status', 'channel'],
    'commercial_outreach': ['outreach_date', 'subject', 'status', 'channel'],
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def query(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    try:
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        else:
            rows = []
    except:
        rows = []
    conn.commit()
    conn.close()
    return rows

def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None

def query_val(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    val = cur.fetchone()
    conn.close()
    return val[0] if val else 0
def query_insert(sql, params=()):
    """Execute INSERT and return the new id."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    new_id = cur.fetchone()[0] if cur.description else None
    cur.close()
    return new_id


def get_credits():
    """Check ZeroBounce credits."""
    import requests
    resp = requests.get('https://api.zerobounce.net/v2/getcredits?api_key=11bd8545466c4a32b99a9446fc28632c', timeout=10)
    return resp.json() if resp.status_code == 200 else {'Credits': '?'}

def validate_email(email):
    """Validate single email via ZeroBounce."""
    import requests
    resp = requests.get(f'https://api.zerobounce.net/v2/validate?api_key=11bd8545466c4a32b99a9446fc28632c&email={email}', timeout=15)
    return resp.json() if resp.status_code == 200 else {'status': 'error'}

def paginate(table, base_sql, count_sql, params, page, sort, order):
    page = max(1, page)
    if sort not in ALLOWED_SORT_COLS.get(table, []) or order not in ('asc', 'desc'):
        sort = 'id'
        order = 'asc'
    total = query_val(count_sql, params)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE
    sql = base_sql + f" ORDER BY {sort} {order} LIMIT {PAGE_SIZE} OFFSET {offset}"
    rows = query(sql, params)
    return rows, total, page, total_pages, sort, order

# ── Commercial ──────────────────────────────────────────────────

@app.route('/')
def index():
    stats = {
        'companies': query_val("SELECT count(*) FROM companies"),
        'contacts': query_val("SELECT count(*) FROM contacts"),
        'interactions': query_val("SELECT count(*) FROM interactions"),
        'research': query_val("SELECT count(*) FROM contacts WHERE needs_research = true"),
    }
    return render_template('index.html', stats=stats, section='commercial', active_page='index')

@app.route('/companies')
def companies_list():
    q = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    sort = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    if q:
        base_sql = "SELECT c.*, (SELECT count(*) FROM contacts WHERE company_id=c.id) as contact_count FROM companies c WHERE c.name ILIKE %s OR c.sector ILIKE %s OR c.region ILIKE %s OR c.business_type ILIKE %s"
        count_sql = "SELECT count(*) FROM companies c WHERE c.name ILIKE %s OR c.sector ILIKE %s OR c.region ILIKE %s OR c.business_type ILIKE %s"
        params = (f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%')
    else:
        base_sql = "SELECT c.*, (SELECT count(*) FROM contacts WHERE company_id=c.id) as contact_count FROM companies c"
        count_sql = "SELECT count(*) FROM companies"
        params = ()
    rows, total, page, total_pages, sort, order = paginate('companies', base_sql, count_sql, params, page, sort, order)
    return render_template('companies.html', companies=rows, query=q, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='commercial', active_page='companies')

@app.route('/companies/add', methods=['GET', 'POST'])
@app.route('/companies/<int:id>/edit', methods=['GET', 'POST'])
def company_form(id=None):
    company = query_one("SELECT * FROM companies WHERE id=%s", (id,)) if id else None
    if id and not company: flash('Company not found', 'error'); return redirect('/companies')
    if request.method == 'POST':
        name = request.form['name']; sector = request.form.get('sector','') or None
        region = request.form.get('region','') or None; website = request.form.get('website','') or None
        source_file = request.form.get('source_file','') or None
        business_type = request.form.get('business_type','') or None
        if id: query("UPDATE companies SET name=%s, sector=%s, region=%s, website=%s, source_file=%s, business_type=%s WHERE id=%s", (name,sector,region,website,source_file,business_type,id))
        else: query("INSERT INTO companies (name, sector, region, website, source_file, business_type) VALUES (%s,%s,%s,%s,%s,%s)", (name,sector,region,website,source_file,business_type))
        flash('Company saved!', 'success'); return redirect('/companies')
    return render_template('company_form.html', company=company, section='commercial', active_page='companies')

@app.route('/companies/<int:id>/delete', methods=['POST'])
def company_delete(id): query("DELETE FROM companies WHERE id=%s", (id,)); flash('Company deleted.', 'success'); return redirect('/companies')

@app.route('/contacts')
def contacts_list():
    q = request.args.get('q', ''); company_id = request.args.get('company_id', '')
    page = int(request.args.get('page', 1)); sort = request.args.get('sort', 'last_name'); order = request.args.get('order', 'asc')
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(co.first_name ILIKE %s OR co.last_name ILIKE %s OR co.email ILIKE %s OR co.role ILIKE %s)"); params.extend([f'%{q}%']*4)
    if company_id: where_parts.append("co.company_id = %s"); params.append(int(company_id))
    where_clause = " AND ".join(where_parts)
    base_sql = f"SELECT co.*, c.name as company_name FROM contacts co LEFT JOIN companies c ON co.company_id=c.id WHERE {where_clause}"
    count_sql = f"SELECT count(*) FROM contacts co WHERE {where_clause}"
    rows, total, page, total_pages, sort, order = paginate('contacts', base_sql, count_sql, tuple(params), page, sort, order)
    return render_template('contacts.html', contacts=rows, query=q, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='commercial', active_page='contacts')

@app.route('/contacts/add', methods=['GET', 'POST'])
@app.route('/contacts/<int:id>/edit', methods=['GET', 'POST'])
def contact_form(id=None):
    contact = query_one("SELECT * FROM contacts WHERE id=%s", (id,)) if id else None
    if id and not contact: flash('Contact not found', 'error'); return redirect('/contacts')
    if request.method == 'POST':
        data = [request.form['first_name'], request.form['last_name'], request.form.get('company_id') or None, request.form.get('role','') or None, request.form.get('email','') or None, request.form.get('phone','') or None, request.form.get('linkedin_url','') or None, request.form.get('needs_research', '1') == '1', request.form.get('source_file','') or None]
        if id: data.append(id); query("UPDATE contacts SET first_name=%s,last_name=%s,company_id=%s,role=%s,email=%s,phone=%s,linkedin_url=%s,needs_research=%s,source_file=%s WHERE id=%s", data)
        else: query("INSERT INTO contacts (first_name,last_name,company_id,role,email,phone,linkedin_url,needs_research,source_file) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
        flash('Contact saved!', 'success'); return redirect('/contacts')
    companies = query("SELECT id, name FROM companies ORDER BY name")
    return render_template('contact_form.html', contact=contact, all_companies=companies, section='commercial', active_page='contacts')

@app.route('/contacts/<int:id>')
def contact_view(id):
    contact = query_one("SELECT co.*, c.name as company_name FROM contacts co LEFT JOIN companies c ON co.company_id=c.id WHERE co.id=%s", (id,))
    if not contact: flash('Contact not found', 'error'); return redirect('/contacts')
    interactions = query("SELECT * FROM interactions WHERE contact_id=%s ORDER BY interaction_date DESC", (id,))
    return render_template('contact_view.html', contact=contact, interactions=interactions, section='commercial', active_page='contacts')

@app.route('/contacts/<int:id>/delete', methods=['POST'])
def contact_delete(id): query("DELETE FROM contacts WHERE id=%s", (id,)); flash('Contact deleted.', 'success'); return redirect('/contacts')

@app.route('/contacts/<int:id>/interactions/add', methods=['GET', 'POST'])
def interaction_add(id):
    contact = query_one("SELECT * FROM contacts WHERE id=%s", (id,))
    if not contact: flash('Contact not found', 'error'); return redirect('/contacts')
    if request.method == 'POST': query("INSERT INTO interactions (contact_id, interaction_date, channel, notes, next_action) VALUES (%s,%s,%s,%s,%s)", (id, request.form.get('interaction_date') or None, request.form.get('channel','') or None, request.form.get('notes','') or None, request.form.get('next_action','') or None)); flash('Interaction logged!', 'success'); return redirect(f'/contacts/{id}')
    return render_template('interaction_form.html', contact=contact, section='commercial', active_page='contacts')

# ── Commercial Outreach ─────────────────────────────────────────

@app.route('/commercial/outreach')
def commercial_outreach_list():
    q = request.args.get('q', ''); status = request.args.get('status', '')
    sector_filter = request.args.get('sector', ''); is_customer_filter = request.args.get('is_customer', '')
    page = int(request.args.get('page', 1))
    sort = request.args.get('sort', 'outreach_date'); order = request.args.get('order', 'desc')
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mo.subject ILIKE %s OR mo.notes ILIKE %s)"); params.extend([f'%{q}%']*2)
    if status: where_parts.append("mo.status = %s"); params.append(status)
    if sector_filter: where_parts.append("c.sector = %s"); params.append(sector_filter)
    if is_customer_filter == 'yes': where_parts.append("c.is_existing_customer = true")
    if is_customer_filter == 'no': where_parts.append("(c.is_existing_customer = false OR c.is_existing_customer IS NULL)")
    w = " AND ".join(where_parts)
    if sort not in ALLOWED_SORT_COLS.get('commercial_outreach', []) or order not in ('asc', 'desc'):
        sort = 'outreach_date'; order = 'desc'
    base_sql = f"SELECT mo.*, c.name as company_name, ct.first_name || ' ' || ct.last_name as contact_name FROM commercial_outreach mo LEFT JOIN companies c ON mo.company_id = c.id LEFT JOIN contacts ct ON mo.contact_id = ct.id WHERE {w}"
    count_sql = f"SELECT count(*) FROM commercial_outreach mo LEFT JOIN companies c ON mo.company_id = c.id WHERE {w}"
    total = query_val(count_sql, tuple(params)); total_pages = max(1, math.ceil(total / PAGE_SIZE)); page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE
    rows = query(base_sql + f" ORDER BY {sort} {order} NULLS LAST LIMIT {PAGE_SIZE} OFFSET {offset}", tuple(params))
    statuses = query("SELECT DISTINCT status FROM commercial_outreach ORDER BY status")
    sectors = query("SELECT DISTINCT sector FROM companies WHERE sector IS NOT NULL ORDER BY sector")
    
    recent_interactions = query("""
        SELECT i.*, co.first_name, co.last_name, co.email,
               c.name as company_name, ecr.campaign_id, ec.name as campaign_name
        FROM interactions i
        JOIN contacts co ON co.id = i.contact_id
        JOIN companies c ON c.id = co.company_id
        LEFT JOIN email_campaign_recipients ecr ON ecr.interaction_id = i.id
        LEFT JOIN email_campaigns ec ON ec.id = ecr.campaign_id
        WHERE i.interaction_date >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY i.interaction_date DESC, i.id DESC
        LIMIT 100
    """)
    
    return render_template('commercial_outreach.html', outreach_records=rows, query=q, status=status, statuses=statuses, sectors=sectors, sector_filter=sector_filter, is_customer_filter=is_customer_filter, page=page, total_pages=total_pages, total=total, sort=sort, order=order, recent_interactions=recent_interactions, section='commercial', active_page='commercial_outreach')

@app.route('/commercial/outreach/add', methods=['GET', 'POST'])
@app.route('/commercial/outreach/<int:id>/edit', methods=['GET', 'POST'])
def commercial_outreach_form(id=None):
    record = query_one("SELECT * FROM commercial_outreach WHERE id=%s", (id,)) if id else None
    if id and not record: flash('Outreach record not found', 'error'); return redirect('/commercial/outreach')
    if request.method == 'POST':
        f = [request.form.get('company_id') or None, request.form.get('contact_id') or None, request.form.get('outreach_date') or None, request.form.get('channel','') or None, request.form.get('subject','') or None, request.form.get('response','') or None, request.form.get('follow_up_date') or None, request.form.get('status','Not Contacted'), request.form.get('notes','') or None, request.form.get('next_action','') or None]
        cols = "company_id,contact_id,outreach_date,channel,subject,response,follow_up_date,status,notes,next_action"
        if id:
            f.append(id)
            query(f"UPDATE commercial_outreach SET {','.join(c+'=%s' for c in cols.split(','))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO commercial_outreach ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Outreach record saved!', 'success'); return redirect('/commercial/outreach')
    companies = query("SELECT id, name FROM companies ORDER BY name")
    contacts = query("SELECT id, first_name || ' ' || last_name as display_name FROM contacts ORDER BY first_name, last_name")
    sl = ['Not Contacted','Contacted','Response Received','Won','Lost','Archived','Plan Phase']
    channels = ['Email','Phone','In-Person','Video Conference','Conference','Site Visit','LinkedIn']
    return render_template('commercial_outreach_form.html', record=record, all_companies=companies, all_contacts=contacts, statuses=sl, channels=channels, section='commercial', active_page='commercial_outreach')

@app.route('/commercial/outreach/<int:id>/delete', methods=['POST'])
def commercial_outreach_delete(id): query("DELETE FROM commercial_outreach WHERE id=%s", (id,)); flash('Outreach record deleted.', 'success'); return redirect('/commercial/outreach')

# ── Email Campaigns ─────────────────────────────────────────

@app.route('/commercial/email-campaigns')
def commercial_email_campaigns_list():
    campaigns = query("""
        SELECT ec.*,
            (SELECT count(*) FROM email_campaign_recipients WHERE campaign_id=ec.id) as recipient_count
        FROM email_campaigns ec
        WHERE ec.audience_type = 'commercial'
        ORDER BY ec.created_at DESC
    """)
    return render_template('commercial_email_campaigns.html', campaigns=campaigns,
                          section='commercial', active_page='commercial_email_campaigns')

@app.route('/commercial/email-campaigns/<int:id>')
def commercial_email_campaign_detail(id):
    campaign = query_one("SELECT * FROM email_campaigns WHERE id=%s", (id,))
    if not campaign:
        flash('Campaign not found', 'error'); return redirect('/commercial/email-campaigns')
    recipients = query("""
        SELECT ecr.*, i.interaction_date, i.channel, i.notes, i.next_action,
               co.first_name, co.last_name, co.email, co.role,
               c.name as company_name
        FROM email_campaign_recipients ecr
        JOIN interactions i ON i.id = ecr.interaction_id
        JOIN contacts co ON co.id = ecr.contact_id
        JOIN companies c ON c.id = co.company_id
        WHERE ecr.campaign_id = %s
        ORDER BY co.last_name, co.first_name
    """, (id,))
    return render_template('commercial_email_campaign_detail.html',
                          campaign=campaign, recipients=recipients,
                          section='commercial', active_page='commercial_email_campaigns')

# ── Commercial Opportunities ─────────────────────────────────────

@app.route('/commercial/opportunities')
def commercial_opportunities_list():
    q = request.args.get('q', ''); phase = request.args.get('phase', '')
    page = int(request.args.get('page', 1))
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mo.opportunity_name ILIKE %s)"); params.append(f'%{q}%')
    if phase: where_parts.append("mo.phase = %s"); params.append(phase)
    w = " AND ".join(where_parts)
    base_sql = f"SELECT mo.*, c.name as company_name FROM commercial_opportunities mo LEFT JOIN companies c ON mo.company_id = c.id WHERE {w}"
    count_sql = f"SELECT count(*) FROM commercial_opportunities mo WHERE {w}"
    total = query_val(count_sql, tuple(params)); total_pages = max(1, math.ceil(total / PAGE_SIZE)); page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE
    rows = query(base_sql + f" ORDER BY mo.created_at DESC LIMIT {PAGE_SIZE} OFFSET {offset}", tuple(params))
    phases = query("SELECT DISTINCT phase FROM commercial_opportunities WHERE phase IS NOT NULL ORDER BY phase")
    return render_template('commercial_opportunities.html', opportunities=rows, query=q, phase=phase, phases=phases, page=page, total_pages=total_pages, total=total, section='commercial', active_page='commercial_outreach')

@app.route('/commercial/opportunities/add', methods=['GET', 'POST'])
@app.route('/commercial/opportunities/<int:id>/edit', methods=['GET', 'POST'])
def commercial_opportunity_form(id=None):
    opp = query_one("SELECT * FROM commercial_opportunities WHERE id=%s", (id,)) if id else None
    if id and not opp: flash('Opportunity not found', 'error'); return redirect('/commercial/opportunities')
    if request.method == 'POST':
        f = [request.form.get('company_id') or None, request.form['opportunity_name'], request.form.get('contract_value') or None, request.form.get('phase','') or None, request.form.get('estimated_award') or None, int(request.form.get('probability', 0)), request.form.get('service_type','') or None, request.form.get('notes','') or None]
        cols = "company_id,opportunity_name,contract_value,phase,estimated_award,probability,service_type,notes"
        if id:
            f.append(id)
            query(f"UPDATE commercial_opportunities SET {','.join(c+'=%s' for c in cols.split(','))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO commercial_opportunities ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Opportunity saved!', 'success'); return redirect('/commercial/opportunities')
    companies = query("SELECT id, name FROM companies ORDER BY name")
    pl = ['Identification','Qualification','Capture','Proposal','Submitted','Awarded','Lost','Closed']
    return render_template('commercial_opportunity_form.html', opp=opp, all_companies=companies, phases=pl, section='commercial', active_page='commercial_outreach')

@app.route('/commercial/opportunities/<int:id>/delete', methods=['POST'])
def commercial_opportunity_delete(id): query("DELETE FROM commercial_opportunities WHERE id=%s", (id,)); flash('Opportunity deleted.', 'success'); return redirect('/commercial/opportunities')

# ── Military ────────────────────────────────────────────────────

@app.route('/military')
def military_dashboard():
    stats = {
        'bases': query_val("SELECT count(*) FROM military_bases"),
        'contacts': query_val("SELECT count(*) FROM military_contacts"),
        'outreach': query_val("SELECT count(*) FROM military_outreach WHERE status NOT IN ('Not Contacted','Archived','Plan Phase')"),
        'priority': query_val("SELECT count(*) FROM military_bases WHERE priority = true"),
    }
    branch_stats = query("SELECT branch, count(*) as cnt FROM military_bases GROUP BY branch ORDER BY cnt DESC")
    recent = query("""
        SELECT mo.*, mb.base_name, mc.contact_name
        FROM military_outreach mo
        LEFT JOIN military_bases mb ON mo.base_id = mb.id
        LEFT JOIN military_contacts mc ON mo.contact_id = mc.id
        WHERE mo.status != 'Plan Phase'
        ORDER BY mo.created_at DESC LIMIT 15
    """)
    return render_template('military_dashboard.html', stats=stats, branch_stats=branch_stats, recent_outreach=recent, section='military', active_page='military_dashboard')

@app.route('/military/bases')
def military_bases_list():
    q = request.args.get('q', ''); branch = request.args.get('branch', ''); state = request.args.get('state', ''); priority = request.args.get('priority', '')
    page = int(request.args.get('page', 1)); sort = request.args.get('sort', 'base_name'); order = request.args.get('order', 'asc')
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mb.base_name ILIKE %s OR mb.city ILIKE %s OR mb.command_name ILIKE %s)"); params.extend([f'%{q}%']*3)
    if branch: where_parts.append("mb.branch = %s"); params.append(branch)
    if state: where_parts.append("mb.state = %s"); params.append(state)
    if priority: where_parts.append("mb.priority = true")
    w = " AND ".join(where_parts)
    rows, total, page, total_pages, sort, order = paginate('military_bases', f"SELECT mb.*, (SELECT count(*) FROM military_contacts WHERE base_id=mb.id) as contact_count FROM military_bases mb WHERE {w}", f"SELECT count(*) FROM military_bases mb WHERE {w}", tuple(params), page, sort, order)
    branches = query("SELECT DISTINCT branch FROM military_bases WHERE branch IS NOT NULL ORDER BY branch")
    states = query("SELECT DISTINCT state FROM military_bases WHERE state IS NOT NULL ORDER BY state")
    return render_template('military_bases.html', bases=rows, query=q, branch=branch, state=state, priority=priority, branches=branches, states=states, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='military', active_page='military_bases')

@app.route('/military/bases/add', methods=['GET', 'POST'])
@app.route('/military/bases/<int:id>/edit', methods=['GET', 'POST'])
def military_base_form(id=None):
    base = query_one("SELECT * FROM military_bases WHERE id=%s", (id,)) if id else None
    if id and not base: flash('Base not found', 'error'); return redirect('/military/bases')
    if request.method == 'POST':
        f = [
            request.form['base_name'], request.form.get('branch','') or None, request.form.get('state','') or None,
            request.form.get('country','USA'), request.form.get('city','') or None, request.form.get('command_name','') or None,
            request.form.get('small_business_office','') or None, request.form.get('contracting_office','') or None,
            request.form.get('sb_office_email','') or None, request.form.get('sb_office_phone','') or None,
            request.form.get('website','') or None, request.form.get('date_verified') or None,
            request.form.get('status','Active'), request.form.get('opportunity_notes','') or None,
            request.form.get('next_action','') or None, request.form.get('notes','') or None,
            request.form.get('priority') == '1'
        ]
        cols = "base_name,branch,state,country,city,command_name,small_business_office,contracting_office,sb_office_email,sb_office_phone,website,date_verified,status,opportunity_notes,next_action,notes,priority"
        if id:
            f.append(id)
            query(f"UPDATE military_bases SET {','.join(c+'=%s' for c in cols.split(','))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO military_bases ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Base saved!', 'success'); return redirect('/military/bases')
    return render_template('military_base_form.html', base=base, section='military', active_page='military_bases')

@app.route('/military/bases/<int:id>')
def military_base_view(id):
    base = query_one("SELECT * FROM military_bases WHERE id=%s", (id,))
    if not base: flash('Base not found', 'error'); return redirect('/military/bases')
    contacts = query("SELECT * FROM military_contacts WHERE base_id=%s ORDER BY contact_name", (id,))
    outreach = query("SELECT mo.*, mc.contact_name FROM military_outreach mo LEFT JOIN military_contacts mc ON mo.contact_id=mc.id WHERE mo.base_id=%s ORDER BY mo.outreach_date DESC NULLS LAST", (id,))
    opps = query("SELECT * FROM military_opportunities WHERE base_id=%s ORDER BY created_at DESC", (id,))
    return render_template('military_base_view.html', base=base, contacts=contacts, outreach=outreach, opportunities=opps, section='military', active_page='military_bases')

@app.route('/military/bases/<int:id>/delete', methods=['POST'])
def military_base_delete(id): query("DELETE FROM military_bases WHERE id=%s", (id,)); flash('Base deleted.', 'success'); return redirect('/military/bases')

@app.route('/military/contacts')
def military_contacts_list():
    q = request.args.get('q', ''); base_id = request.args.get('base_id', '')
    page = int(request.args.get('page', 1)); sort = request.args.get('sort', 'contact_name'); order = request.args.get('order', 'asc')
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mc.contact_name ILIKE %s OR mc.title ILIKE %s OR mc.email ILIKE %s OR mc.notes ILIKE %s)"); params.extend([f'%{q}%']*4)
    if base_id: where_parts.append("mc.base_id = %s"); params.append(int(base_id))
    w = " AND ".join(where_parts)
    rows, total, page, total_pages, sort, order = paginate('military_contacts', f"SELECT mc.*, mb.base_name FROM military_contacts mc LEFT JOIN military_bases mb ON mc.base_id=mb.id WHERE {w}", f"SELECT count(*) FROM military_contacts mc WHERE {w}", tuple(params), page, sort, order)
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    return render_template('military_contacts.html', contacts=rows, query=q, base_id=base_id, all_bases=bases, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='military', active_page='military_contacts')

@app.route('/military/contacts/add', methods=['GET', 'POST'])
@app.route('/military/contacts/<int:id>/edit', methods=['GET', 'POST'])
def military_contact_form(id=None):
    contact = query_one("SELECT * FROM military_contacts WHERE id=%s", (id,)) if id else None
    if id and not contact: flash('Contact not found', 'error'); return redirect('/military/contacts')
    if request.method == 'POST':
        f = [request.form.get('base_id') or None, request.form['contact_name'], request.form.get('title','') or None, request.form.get('email','') or None, request.form.get('phone','') or None, request.form.get('contact_role','Small Business POC'), request.form.get('decision_maker') == '1', request.form.get('notes','') or None, request.form.get('needs_followup') == '1']
        cols = "base_id,contact_name,title,email,phone,contact_role,decision_maker,notes,needs_followup"
        if id:
            f.append(id)
            query(f"UPDATE military_contacts SET {','.join(c+'=%s' for c in cols.split(','))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO military_contacts ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Contact saved!', 'success'); return redirect('/military/contacts')
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    return render_template('military_contact_form.html', contact=contact, all_bases=bases, section='military', active_page='military_contacts')

@app.route('/military/contacts/<int:id>')
def military_contact_view(id):
    contact = query_one("SELECT mc.*, mb.base_name FROM military_contacts mc LEFT JOIN military_bases mb ON mc.base_id=mb.id WHERE mc.id=%s", (id,))
    if not contact: flash('Contact not found', 'error'); return redirect('/military/contacts')
    outreach = query("SELECT * FROM military_outreach WHERE contact_id=%s ORDER BY outreach_date DESC NULLS LAST", (id,))
    return render_template('military_contact_view.html', contact=contact, outreach=outreach, section='military', active_page='military_contacts')

@app.route('/military/contacts/<int:id>/delete', methods=['POST'])
def military_contact_delete(id): query("DELETE FROM military_contacts WHERE id=%s", (id,)); flash('Contact deleted.', 'success'); return redirect('/military/contacts')

@app.route('/military/outreach')
def military_outreach_list():
    q = request.args.get('q', ''); status = request.args.get('status', '')
    page = int(request.args.get('page', 1))
    sort = request.args.get('sort', 'outreach_date'); order = request.args.get('order', 'desc')
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mo.subject ILIKE %s OR mo.notes ILIKE %s)"); params.extend([f'%{q}%']*2)
    if status: where_parts.append("mo.status = %s"); params.append(status)
    w = " AND ".join(where_parts)
    if sort not in ALLOWED_SORT_COLS.get('military_outreach', []) or order not in ('asc', 'desc'):
        sort = 'outreach_date'; order = 'desc'
    base_sql = f"SELECT mo.*, mb.base_name, mc.contact_name FROM military_outreach mo LEFT JOIN military_bases mb ON mo.base_id = mb.id LEFT JOIN military_contacts mc ON mo.contact_id = mc.id WHERE {w}"
    count_sql = f"SELECT count(*) FROM military_outreach mo WHERE {w}"
    total = query_val(count_sql, tuple(params)); total_pages = max(1, math.ceil(total / PAGE_SIZE)); page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE
    rows = query(base_sql + f" ORDER BY {sort} {order} NULLS LAST LIMIT {PAGE_SIZE} OFFSET {offset}", tuple(params))
    statuses = query("SELECT DISTINCT status FROM military_outreach ORDER BY status")
    return render_template('military_outreach.html', outreach_records=rows, query=q, status=status, statuses=statuses, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='military', active_page='military_outreach')

@app.route('/military/outreach/add', methods=['GET', 'POST'])
@app.route('/military/outreach/<int:id>/edit', methods=['GET', 'POST'])
def military_outreach_form(id=None):
    record = query_one("SELECT * FROM military_outreach WHERE id=%s", (id,)) if id else None
    if id and not record: flash('Outreach record not found', 'error'); return redirect('/military/outreach')
    if request.method == 'POST':
        f = [request.form.get('contact_id') or None, request.form.get('base_id') or None, request.form.get('capability_briefing_requested') == '1', request.form.get('outreach_date') or None, request.form.get('channel','') or None, request.form.get('subject','') or None, request.form.get('response','') or None, request.form.get('briefing_scheduled') or None, request.form.get('follow_up_date') or None, request.form.get('status','Not Contacted'), request.form.get('notes','') or None, request.form.get('next_action','') or None]
        cols = "contact_id,base_id,capability_briefing_requested,outreach_date,channel,subject,response,briefing_scheduled,follow_up_date,status,notes,next_action"
        if id:
            f.append(id)
            query(f"UPDATE military_outreach SET {','.join(c+'=%s' for c in cols.split(','))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO military_outreach ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Outreach record saved!', 'success'); return redirect('/military/outreach')
    contacts = query("SELECT id, contact_name, title FROM military_contacts ORDER BY contact_name")
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    sl = ['Not Contacted','Contacted','Response Received','Briefing Scheduled','Briefing Completed','Won','Lost','Archived','Plan Phase']
    channels = ['Email','Phone','In-Person','Video Conference','Conference','Site Visit','Capabilities Briefing','LinkedIn','SAM.gov']
    return render_template('military_outreach_form.html', record=record, all_contacts=contacts, all_bases=bases, statuses=sl, channels=channels, section='military', active_page='military_outreach')

@app.route('/military/outreach/<int:id>/delete', methods=['POST'])
def military_outreach_delete(id): query("DELETE FROM military_outreach WHERE id=%s", (id,)); flash('Outreach record deleted.', 'success'); return redirect('/military/outreach')

@app.route('/military/opportunities')
def military_opportunities_list():
    q = request.args.get('q', ''); phase = request.args.get('phase', '')
    page = int(request.args.get('page', 1))
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mo.opportunity_name ILIKE %s OR mo.solicitation_number ILIKE %s)"); params.extend([f'%{q}%']*2)
    if phase: where_parts.append("mo.phase = %s"); params.append(phase)
    w = " AND ".join(where_parts)
    base_sql = f"SELECT mo.*, mb.base_name FROM military_opportunities mo LEFT JOIN military_bases mb ON mo.base_id = mb.id WHERE {w}"
    count_sql = f"SELECT count(*) FROM military_opportunities mo WHERE {w}"
    total = query_val(count_sql, tuple(params)); total_pages = max(1, math.ceil(total / PAGE_SIZE)); page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE
    rows = query(base_sql + f" ORDER BY mo.created_at DESC LIMIT {PAGE_SIZE} OFFSET {offset}", tuple(params))
    phases = query("SELECT DISTINCT phase FROM military_opportunities WHERE phase IS NOT NULL ORDER BY phase")
    return render_template('military_opportunities.html', opportunities=rows, query=q, phase=phase, phases=phases, page=page, total_pages=total_pages, total=total, section='military', active_page='military_outreach')

@app.route('/military/opportunities/add', methods=['GET', 'POST'])
@app.route('/military/opportunities/<int:id>/edit', methods=['GET', 'POST'])
def military_opportunity_form(id=None):
    opp = query_one("SELECT * FROM military_opportunities WHERE id=%s", (id,)) if id else None
    if id and not opp: flash('Opportunity not found', 'error'); return redirect('/military/opportunities')
    if request.method == 'POST':
        f = [request.form.get('base_id') or None, request.form['opportunity_name'], request.form.get('solicitation_number','') or None, request.form.get('contract_value') or None, request.form.get('phase','') or None, request.form.get('estimated_award') or None, int(request.form.get('probability', 0)), request.form.get('service_type','') or None, request.form.get('notes','') or None]
        cols = "base_id,opportunity_name,solicitation_number,contract_value,phase,estimated_award,probability,service_type,notes"
        if id:
            f.append(id)
            query(f"UPDATE military_opportunities SET {','.join(c+'=%s' for c in cols.split(','))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO military_opportunities ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Opportunity saved!', 'success'); return redirect('/military/opportunities')
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    pl = ['Identification','Qualification','Capture','Proposal','Submitted','Awarded','Lost','Closed']
    return render_template('military_opportunity_form.html', opp=opp, all_bases=bases, phases=pl, section='military', active_page='military_outreach')

@app.route('/military/opportunities/<int:id>/delete', methods=['POST'])
def military_opportunity_delete(id): query("DELETE FROM military_opportunities WHERE id=%s", (id,)); flash('Opportunity deleted.', 'success'); return redirect('/military/opportunities')

# ── Placeholders ────────────────────────────────────────────────

def placeholder(title, section_name, page_name):
    return render_template('placeholder.html', title=title, section=section_name, active_page=page_name)

@app.route('/sales/pipeline')
def sales_pipeline(): return placeholder('Sales Pipeline', 'sales', 'sales_pipeline')
@app.route('/sales/deals')
def sales_deals(): return placeholder('Deals', 'sales', 'sales_deals')
@app.route('/sales/quotes')
def sales_quotes(): return placeholder('Quotes', 'sales', 'sales_quotes')
@app.route('/marketing/campaigns')
def marketing_campaigns():
    stats = {
        'total_campaigns': query_val("SELECT count(*) FROM email_campaigns"),
        'total_sent': query_val("SELECT coalesce(sum(total_recipients), 0) FROM email_campaigns"),
        'total_opened': query_val("SELECT coalesce(sum(total_opened), 0) FROM email_campaigns"),
    }
    stats['open_rate'] = stats['total_opened'] / stats['total_sent'] * 100 if stats['total_sent'] > 0 else 0
    campaigns = query("SELECT * FROM email_campaigns ORDER BY created_at DESC")
    import json
    campaigns_json = json.dumps([{
        'id': c['id'], 'name': c['name'], 'total_recipients': c['total_recipients'] or 0,
        'total_opened': c['total_opened'] or 0, 'total_clicked': c['total_clicked'] or 0,
        'total_bounced': c['total_bounced'] or 0, 'total_unsubscribed': c['total_unsubscribed'] or 0
    } for c in campaigns])
    return render_template('campaigns.html', stats=stats, campaigns=campaigns, campaigns_json=campaigns_json, section='marketing', active_page='marketing_campaigns')

@app.route('/marketing/campaigns/add', methods=['GET', 'POST'])
@app.route('/marketing/campaigns/<int:id>/edit', methods=['GET', 'POST'])
def marketing_campaign_form(id=None):
    campaign = query_one("SELECT * FROM email_campaigns WHERE id=%s", (id,)) if id else None
    if id and not campaign: flash('Campaign not found', 'error'); return redirect('/marketing/campaigns')
    if request.method == 'POST':
        data = {
            'name': request.form['name'],
            'subject_line': request.form.get('subject_line') or None,
            'sender_email': request.form.get('sender_email') or None,
            'template_used': request.form.get('template_used') or None,
            'audience_type': request.form.get('audience_type', 'commercial'),
            'status': request.form.get('status', 'draft'),
            'scheduled_at': request.form.get('scheduled_at') or None,
            'sent_at': request.form.get('sent_at') or None,
            'total_recipients': int(request.form.get('total_recipients', 0)),
            'notes': request.form.get('notes') or None,
        }
        if id:
            sets = ', '.join(f"{k}=%s" for k in data)
            vals = list(data.values()) + [id]
            query(f"UPDATE email_campaigns SET {sets}, updated_at=CURRENT_TIMESTAMP WHERE id=%s", vals)
        else:
            cols = ', '.join(data.keys())
            phs = ', '.join(['%s'] * len(data))
            query(f"INSERT INTO email_campaigns ({cols}) VALUES ({phs})", list(data.values()))
        flash('Campaign saved!', 'success'); return redirect('/marketing/campaigns')
    return render_template('campaign_form.html', campaign=campaign, section='marketing', active_page='marketing_campaigns')

@app.route('/marketing/campaigns/<int:id>')
def marketing_campaign_view(id):
    campaign = query_one("SELECT * FROM email_campaigns WHERE id=%s", (id,))
    if not campaign: flash('Campaign not found', 'error'); return redirect('/marketing/campaigns')
    sends = query("""
        SELECT es.*, c.name as company_name, mb.base_name
        FROM email_sends es
        LEFT JOIN companies c ON es.company_id = c.id
        LEFT JOIN military_bases mb ON es.military_base_id = mb.id
        WHERE es.campaign_id = %s
        ORDER BY es.sent_at DESC NULLS LAST
    """, (id,))
    import json
    total = campaign['total_recipients'] or 0
    opened = campaign['total_opened'] or 0
    clicked = campaign['total_clicked'] or 0
    bounced = campaign['total_bounced'] or 0
    unsub = campaign['total_unsubscribed'] or 0
    no_eng = max(0, total - opened - bounced - unsub)
    chart_data = json.dumps({
        'total': total, 'opened': opened, 'clicked': clicked,
        'bounced': bounced, 'unsubscribed': unsub, 'no_engagement': no_eng
    })
    return render_template('campaign_view.html', campaign=campaign, sends=sends,
                           chart_data=chart_data, section='marketing', active_page='marketing_campaigns')

@app.route('/marketing/campaigns/<int:id>/delete', methods=['POST'])
def marketing_campaign_delete(id):
    query("DELETE FROM email_campaigns WHERE id=%s", (id,))
    flash('Campaign deleted.', 'success'); return redirect('/marketing/campaigns')

@app.route('/marketing/campaigns/<int:id>/sends/add', methods=['GET', 'POST'])
def marketing_send_add(id):
    campaign = query_one("SELECT * FROM email_campaigns WHERE id=%s", (id,))
    if not campaign: flash('Campaign not found', 'error'); return redirect('/marketing/campaigns')
    if request.method == 'POST':
        _save_email_send(id, None)
        flash('Send logged!', 'success'); return redirect(f'/marketing/campaigns/{id}')
    companies = query("SELECT id, name FROM companies ORDER BY name")
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    return render_template('campaign_send_form.html', campaign=campaign, send=None,
                           companies=companies, bases=bases, section='marketing', active_page='marketing_campaigns')

@app.route('/marketing/campaigns/<int:id>/sends/<int:send_id>/edit', methods=['GET', 'POST'])
def marketing_send_edit(id, send_id):
    campaign = query_one("SELECT * FROM email_campaigns WHERE id=%s", (id,))
    if not campaign: flash('Campaign not found', 'error'); return redirect('/marketing/campaigns')
    send = query_one("SELECT * FROM email_sends WHERE id=%s", (send_id,))
    if not send: flash('Send not found', 'error'); return redirect(f'/marketing/campaigns/{id}')
    if request.method == 'POST':
        _save_email_send(id, send_id)
        flash('Send updated!', 'success'); return redirect(f'/marketing/campaigns/{id}')
    companies = query("SELECT id, name FROM companies ORDER BY name")
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    return render_template('campaign_send_form.html', campaign=campaign, send=send,
                           companies=companies, bases=bases, section='marketing', active_page='marketing_campaigns')

def _save_email_send(campaign_id, send_id):
    data = {
        'campaign_id': campaign_id,
        'contact_type': request.form.get('contact_type', 'commercial'),
        'company_id': request.form.get('company_id') or None,
        'military_base_id': request.form.get('military_base_id') or None,
        'recipient_email': request.form.get('recipient_email'),
        'recipient_name': request.form.get('recipient_name') or None,
        'sent_at': request.form.get('sent_at') or None,
        'opened_at': request.form.get('opened_at') or None,
        'clicked_at': request.form.get('clicked_at') or None,
        'bounced': request.form.get('bounced') == '1',
        'unsubscribed': request.form.get('unsubscribed') == '1',
    }
    if send_id:
        sets = ', '.join(f"{k}=%s" for k in data)
        vals = list(data.values()) + [send_id]
        query(f"UPDATE email_sends SET {sets} WHERE id=%s", vals)
    else:
        cols = ', '.join(data.keys())
        phs = ', '.join(['%s'] * len(data))
        query(f"INSERT INTO email_sends ({cols}) VALUES ({phs})", list(data.values()))
    # Recompute campaign aggregates
    query("""
        UPDATE email_campaigns SET
            total_recipients = (SELECT count(*) FROM email_sends WHERE campaign_id=%s),
            total_opened = (SELECT count(*) FROM email_sends WHERE campaign_id=%s AND opened_at IS NOT NULL),
            total_clicked = (SELECT count(*) FROM email_sends WHERE campaign_id=%s AND clicked_at IS NOT NULL),
            total_bounced = (SELECT count(*) FROM email_sends WHERE campaign_id=%s AND bounced=true),
            total_unsubscribed = (SELECT count(*) FROM email_sends WHERE campaign_id=%s AND unsubscribed=true),
            updated_at = CURRENT_TIMESTAMP
        WHERE id=%s
    """, (campaign_id, campaign_id, campaign_id, campaign_id, campaign_id, campaign_id))

@app.route('/marketing/leads')
def marketing_leads(): return placeholder('Leads', 'marketing', 'marketing_leads')
@app.route('/support/tickets')
def support_tickets(): return placeholder('Support Tickets', 'support', 'support_tickets')
@app.route('/support/kb')
def support_kb(): return placeholder('Knowledge Base', 'support', 'support_kb')
@app.route('/reports/analytics')
def reports_analytics(): return placeholder('Analytics', 'reports', 'reports_analytics')
@app.route('/reports/dashboards')
def reports_dashboards(): return placeholder('Custom Dashboards', 'reports', 'reports_dashboards')
@app.route('/admin/settings')
def admin_settings(): return placeholder('Settings', 'admin', 'admin_settings')
@app.route('/admin/users')
def admin_users(): return placeholder('User Management', 'admin', 'admin_users')
@app.route('/admin/audit')
def admin_audit(): return placeholder('Audit Log', 'admin', 'admin_audit')

# ── Campaign Builder (ZeroBounce + Brevo) ─────────────────────

@app.route('/commercial/campaigns')
def campaign_list():
    campaigns = query("""
        SELECT c.*, 
               (SELECT count(*) FROM campaign_recipients WHERE campaign_id = c.id) as recipient_count
        FROM campaigns c 
        ORDER BY c.created_at DESC
    """)
    return render_template('campaign_list.html', campaigns=campaigns, 
                          section='commercial', active_page='commercial_campaigns')

def sync_commercial_to_marketing(campaign_id):
    """Sync a commercial campaign to the marketing email_campaigns table."""
    c = query_one("SELECT * FROM campaigns WHERE id=%s", (campaign_id,))
    if not c:
        return
    existing = query_one("SELECT id FROM email_campaigns WHERE name=%s AND created_at::date = %s::date",
                        (c['name'], c['created_at'].strftime('%Y-%m-%d') if c['created_at'] else None))
    if existing:
        # Update
        query("""
            UPDATE email_campaigns SET
                name=%s, subject_line=%s, sender_email=%s, status=%s,
                description=%s,
                total_recipients = (SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s),
                total_sent = (SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND send_status='sent'),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (c['name'], c.get('subject_template'), c.get('sender_email'),
               'sent' if c.get('status') == 'sent' else 'draft',
               c.get('description'), campaign_id, campaign_id, existing['id']))
    else:
        # Insert new
        query("""
            INSERT INTO email_campaigns (name, subject_line, sender_email, audience_type, status,
                description, total_recipients)
            VALUES (%s, %s, %s, 'commercial', %s, %s,
                (SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s))
        """, (c['name'], c.get('subject_template'), c.get('sender_email'),
               'sent' if c.get('status') == 'sent' else 'draft',
               c.get('description'), campaign_id))

@app.route('/commercial/campaigns/new', methods=['GET', 'POST'])
def campaign_new():
    if request.method == 'POST':
        campaign_id = query_insert("""
            INSERT INTO campaigns (name, description, sender_name, sender_email, 
                   subject_template, body_template, target_sector, target_region, 
                   target_is_customer, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft')
            RETURNING id
        """, (
            request.form.get('name'),
            request.form.get('description'),
            request.form.get('sender_name', 'Ronnie Gaines'),
            request.form.get('sender_email', 'rong@simrobotics.com'),
            request.form.get('subject_template'),
            request.form.get('body_template'),
            request.form.get('target_sector') or None,
            request.form.get('target_region') or None,
            request.form.get('target_is_customer', 'no')
        ))
        sync_commercial_to_marketing(campaign_id)
        flash('Campaign created! Now add recipients.', 'success')
        return redirect(f'/commercial/campaigns/{campaign_id}')
    
    sectors = query("SELECT DISTINCT sector FROM companies WHERE sector IS NOT NULL ORDER BY sector")
    regions = query("SELECT DISTINCT region FROM companies WHERE region IS NOT NULL ORDER BY region")
    return render_template('campaign_form.html', sectors=sectors, regions=regions,
                          section='commercial', active_page='commercial_campaigns')

@app.route('/commercial/campaigns/<int:id>')
def campaign_view(id):
    campaign = query_one("SELECT * FROM campaigns WHERE id=%s", (id,))
    if not campaign: flash('Campaign not found', 'error'); return redirect('/commercial/campaigns')
    
    # Paging & sorting
    page = request.args.get('page', 1, type=int)
    sort_col = request.args.get('sort', 'last_name')
    order = request.args.get('order', 'asc')
    page = max(1, page)
    cols = ['first_name','last_name','email','company_name','role','sector','validation_status','send_status']
    if sort_col not in cols: sort_col = 'last_name'
    if order not in ('asc','desc'): order = 'asc'
    next_order = 'desc' if order == 'asc' else 'asc'
    PAGE_SIZE = 50
    
    stats = {
        'total': query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s", (id,)),
        'validated': query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND validation_status='valid'", (id,)),
        'invalid': query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND validation_status='invalid'", (id,)),
        'pending_validation': query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND (validation_status IS NULL OR validation_status='')", (id,)),
        'sent': query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND send_status='sent'", (id,)),
        'delivered': query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND send_status='delivered'", (id,)),
        'opened': query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND send_status='opened'", (id,)),
        'bounced': query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND send_status='bounced'", (id,)),
    }
    
    total_pages = max(1, (stats['total'] + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE
    
    recipients = query(f"""
        SELECT cr.*, co.first_name, co.last_name, co.role, co.email,
               c.name as company_name, c.sector
        FROM campaign_recipients cr
        JOIN contacts co ON co.id = cr.contact_id
        JOIN companies c ON c.id = co.company_id
        WHERE cr.campaign_id = %s
        ORDER BY {sort_col} {order}
        LIMIT {PAGE_SIZE} OFFSET {offset}
    """, (id,))
    
    resp = app.make_response(render_template('campaign_view.html', campaign=campaign, recipients=recipients,
                          stats=stats, page=page, total_pages=total_pages,
                          sort=sort_col, order=order, next_order=next_order,
                          section='commercial', active_page='commercial_campaigns'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/commercial/campaigns/<int:id>/recipients/<int:recipient_id>/delete', methods=['POST'])
def campaign_recipient_delete(id, recipient_id):
    query("DELETE FROM campaign_recipients WHERE id=%s AND campaign_id=%s", (recipient_id, id))
    flash('Recipient removed.', 'success')
    return redirect(f'/commercial/campaigns/{id}')

@app.route('/commercial/campaigns/<int:id>/recipients', methods=['GET', 'POST'])
def campaign_recipients(id):
    campaign = query_one("SELECT * FROM campaigns WHERE id=%s", (id,))
    if not campaign: flash('Campaign not found', 'error'); return redirect('/commercial/campaigns')
    
    if request.method == 'POST':
        where = ["co.email IS NOT NULL", "co.email != ''"]
        params = []
        
        if campaign.target_sector:
            where.append("c.sector = %s")
            params.append(campaign.target_sector)
        if campaign.target_region:
            where.append("c.region ILIKE %s")
            params.append(f'%{campaign.target_region}%')
        if campaign.target_is_customer == 'no':
            where.append("(c.is_existing_customer = false OR c.is_existing_customer IS NULL)")
        elif campaign.target_is_customer == 'yes':
            where.append("c.is_existing_customer = true")
        
        w = " AND ".join(where)
        
        query(f"""
            INSERT INTO campaign_recipients (campaign_id, contact_id, email)
            SELECT %s, co.id, co.email
            FROM contacts co
            JOIN companies c ON c.id = co.company_id
            WHERE {w}
            AND NOT EXISTS (
                SELECT 1 FROM campaign_recipients cr 
                WHERE cr.campaign_id = %s AND cr.contact_id = co.id
            )
        """, [id] + params + [id])
        
        query("""
            UPDATE campaigns SET 
                total_contacts = (SELECT count(*) FROM campaign_recipients WHERE campaign_id = %s),
                total_companies = (SELECT count(DISTINCT co.company_id) FROM campaign_recipients cr JOIN contacts co ON co.id = cr.contact_id WHERE cr.campaign_id = %s),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (id, id, id))
        
        count = query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id = %s", (id,))
        sync_commercial_to_marketing(id)
        flash(f'{count} recipients added to campaign!', 'success')
        return redirect(f'/commercial/campaigns/{id}')
    
    where = ["co.email IS NOT NULL", "co.email != ''"]
    params = []
    if campaign.target_sector:
        where.append("c.sector = %s")
        params.append(campaign.target_sector)
    if campaign.target_region:
        where.append("c.region ILIKE %s")
        params.append(f'%{campaign.target_region}%')
    if campaign.target_is_customer == 'no':
        where.append("(c.is_existing_customer = false OR c.is_existing_customer IS NULL)")
    elif campaign.target_is_customer == 'yes':
        where.append("c.is_existing_customer = true")
    w = " AND ".join(where)
    
    preview = query(f"""
        SELECT co.id, co.first_name, co.last_name, co.email, co.role,
               c.name as company_name, c.sector, c.region
        FROM contacts co
        JOIN companies c ON c.id = co.company_id
        WHERE {w}
        ORDER BY c.name, co.first_name
        LIMIT 500
    """, params)
    
    return render_template('campaign_recipients.html', campaign=campaign, preview=preview,
                          section='commercial', active_page='commercial_campaigns')

@app.route('/commercial/campaigns/<int:id>/delete', methods=['POST'])
def campaign_delete(id):
    query("DELETE FROM campaign_recipients WHERE campaign_id=%s", (id,))
    query("DELETE FROM campaigns WHERE id=%s", (id,))
    flash('Campaign deleted.', 'success')
    return redirect('/commercial/campaigns')
# ── Campaign Sending (via Brevo) ──────────────────────────────

@app.route('/commercial/campaigns/<int:id>/send', methods=['GET', 'POST'])
def campaign_send(id):
    """Send campaign emails via Brevo."""
    campaign = query_one("SELECT * FROM campaigns WHERE id=%s", (id,))
    if not campaign: flash('Campaign not found', 'error'); return redirect('/commercial/campaigns')
    
    if request.method == 'POST':
        # Get all pending recipients
        recipients = query("""
            SELECT cr.id as cr_id, cr.email, co.first_name, co.last_name, 
                   c.name as company_name
            FROM campaign_recipients cr
            JOIN contacts co ON co.id = cr.contact_id
            JOIN companies c ON c.id = co.company_id
            WHERE cr.campaign_id = %s AND (cr.send_status = 'pending' OR cr.send_status IS NULL)
        """, (id,))
        
        if not recipients:
            flash('No pending recipients to send to.', 'warning')
            return redirect(f'/commercial/campaigns/{id}')
        
        # Build recipient dicts for Brevo
        recip_dicts = [{
            'email': r.email,
            'first_name': r.first_name,
            'last_name': r.last_name,
            'company': r.company_name
        } for r in recipients]
        
        # Get CC list from form
        cc_list = request.form.get('cc', '').split(',') if request.form.get('cc') else []
        cc_list = [e.strip() for e in cc_list if e.strip()]
        
        # Import and use brevo
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'integrations'))
        import brevo
        
        flash_msg = f'Sending {len(recip_dicts)} emails via Brevo...'
        flash(flash_msg, 'info')
        
        results = brevo.send_batch(
            campaign.sender_name or 'Ronnie Gaines',
            campaign.sender_email or 'rong@simrobotics.com',
            recip_dicts,
            campaign.subject_template or 'SimRobotics - BIM/VDC Services',
            campaign.body_template or '<html><body><p>Hello {first_name},</p></body></html>',
            cc=cc_list
        )
        
        # Update campaign_recipients with results
        sent_count = 0
        for i, result in enumerate(results):
            if i < len(recipients):
                cr = recipients[i]
                if result['success']:
                    query("""
                        UPDATE campaign_recipients 
                        SET send_status='sent', sent_at=CURRENT_TIMESTAMP, 
                            brevo_message_id=%s 
                        WHERE id=%s
                    """, (result.get('message_id', ''), cr.cr_id))
                    sent_count += 1
        
        # Update campaign totals
        query("""
            UPDATE campaigns SET 
                total_sent = (SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND send_status='sent'),
                status = 'sent',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (id, id))
        
        # Calculate costs after sending
        calculate_campaign_cost(id)
        
        sync_commercial_to_marketing(id)
        flash(f'Campaign sent! {sent_count} of {len(recip_dicts)} emails delivered via Brevo.', 'success')
        return redirect(f'/commercial/campaigns/{id}')
    
    # GET: show send confirmation page
    pending = query_val("""
        SELECT count(*) FROM campaign_recipients 
        WHERE campaign_id=%s AND (send_status='pending' OR send_status IS NULL)
    """, (id,))
    
    already_sent = query_val("""
        SELECT count(*) FROM campaign_recipients 
        WHERE campaign_id=%s AND send_status='sent'
    """, (id,))
    
    return render_template('campaign_send.html', campaign=campaign, 
                          pending=pending, already_sent=already_sent,
                          section='commercial', active_page='commercial_campaigns')


# ── Campaign Email Validation (ZeroBounce) ────────────────────

@app.route('/commercial/campaigns/<int:id>/validate', methods=['GET', 'POST'])
def campaign_validate(id):
    """Validate campaign recipient emails via ZeroBounce."""
    campaign = query_one("SELECT * FROM campaigns WHERE id=%s", (id,))
    if not campaign: flash('Campaign not found', 'error'); return redirect('/commercial/campaigns')
    
    if request.method == 'POST':
        # Get unvalidated recipients
        recipients = query("""
            SELECT cr.id as cr_id, cr.email
            FROM campaign_recipients cr
            WHERE cr.campaign_id = %s AND (cr.validation_status IS NULL OR cr.validation_status = '')
        """, (id,))
        
        if not recipients:
            flash('No unvalidated recipients.', 'warning')
            return redirect(f'/commercial/campaigns/{id}')
        
        # Check credits first
        zb_credits = get_credits()
        available = int(zb_credits.get('Credits', 0))
        if available < len(recipients):
            flash(f'Not enough ZeroBounce credits! Need {len(recipients)}, have {available}.', 'error')
            return redirect(f'/commercial/campaigns/{id}')
        
        emails = [r.email for r in recipients]
        flash(f'Validating {len(emails)} emails... This may take a minute.', 'info')
        
        # Run validation (do it synchronously but with progress)
        for i, r in enumerate(recipients):
            try:
                result = validate_email(r.email)
                status = result.get('status', 'error')
                sub_status = result.get('sub_status', '')
                
                # Store result
                query("""
                    INSERT INTO email_validations (contact_id, email, status, sub_status, 
                        free_email, did_you_mean, account, domain, domain_age_days, smtp_provider)
                    SELECT cr.contact_id, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    FROM campaign_recipients cr WHERE cr.id = %s
                    ON CONFLICT DO NOTHING
                """, (r.email, status, sub_status,
                      result.get('free_email', False),
                      result.get('did_you_mean'),
                      result.get('account'),
                      result.get('domain'),
                      str(result.get('domain_age_days', '')),
                      result.get('smtp_provider'),
                      r.cr_id))
                
                # Update campaign_recipient
                query("""
                    UPDATE campaign_recipients 
                    SET validation_status = %s
                    WHERE id = %s
                """, (status, r.cr_id))
                
                time.sleep(0.3)  # Rate limit
                
            except Exception as e:
                query("""
                    UPDATE campaign_recipients SET validation_status = 'error', error_message = %s WHERE id = %s
                """, (str(e)[:500], r.cr_id))
        
        # Update campaign counts
        query("""
            UPDATE campaigns SET
                total_validated = (SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND validation_status='valid'),
                status = 'ready',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (id, id))
        
        # Calculate costs after validation
        calculate_campaign_cost(id)
        
        valid_count = query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND validation_status='valid'", (id,))
        invalid_count = query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND validation_status='invalid'", (id,))
        
        sync_commercial_to_marketing(id)
        flash(f'Validation complete! {valid_count} valid, {invalid_count} invalid.', 'success')
        return redirect(f'/commercial/campaigns/{id}')
    
    # GET: show validation preview
    unvalidated = query_val("""
        SELECT count(*) FROM campaign_recipients 
        WHERE campaign_id=%s AND (validation_status IS NULL OR validation_status = '')
    """, (id,))
    
    already_valid = query_val("""
        SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND validation_status='valid'
    """, (id,))
    
    already_invalid = query_val("""
        SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND validation_status='invalid'
    """, (id,))
    
    credits = get_credits() if request.args.get('check','') else {}
    
    return render_template('campaign_validate.html', campaign=campaign,
                          unvalidated=unvalidated, already_valid=already_valid,
                          already_invalid=already_invalid, credits=credits,
                          section='commercial', active_page='commercial_campaigns')

# ── Cost Tracking Dashboard ───────────────────────────────────

def get_cost_rates():
    """Return current cost rates for Brevo and ZeroBounce."""
    return {
        'brevo_monthly_included': 5000,
        'brevo_overage_per_email': 0.013,
        'zerobounce_free_credits': 100,
        'zerobounce_per_email': 0.01
    }

def calculate_campaign_cost(campaign_id):
    """Calculate and store cost for a campaign."""
    rates = get_cost_rates()
    
    # Get campaign stats
    validated = query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND validation_status IS NOT NULL AND validation_status != ''", (campaign_id,)) or 0
    sent = query_val("SELECT count(*) FROM campaign_recipients WHERE campaign_id=%s AND send_status='sent'", (campaign_id,)) or 0
    
    # Calculate ZeroBounce cost (first 100 free, then $0.01 each)
    # Track cumulative credits used across all campaigns
    total_validated_all = query_val("SELECT coalesce(sum(credits_used), 0) FROM campaigns") or 0
    
    # What portion of the free 100 credits has been used already
    free_used_before = min(total_validated_all, rates['zerobounce_free_credits'])
    free_remaining_before = max(0, rates['zerobounce_free_credits'] - free_used_before)
    
    # This campaign's validation
    free_for_this_campaign = min(validated, free_remaining_before)
    paid_for_this_campaign = max(0, validated - free_for_this_campaign)
    zb_cost = round(paid_for_this_campaign * rates['zerobounce_per_email'], 4)
    
    # Calculate Brevo cost (free within monthly limit, then $0.013 each)
    total_sent_all = query_val("SELECT coalesce(sum(total_sent), 0) FROM campaigns") or 0
    sent_before = max(0, total_sent_all - sent)
    free_sends_before = min(sent_before, rates['brevo_monthly_included'])
    free_sends_remaining = max(0, rates['brevo_monthly_included'] - free_sends_before)
    
    free_for_this = min(sent, free_sends_remaining)
    paid_for_this = max(0, sent - free_for_this)
    brevo_cost = round(paid_for_this * rates['brevo_overage_per_email'], 4)
    
    total = round(zb_cost + brevo_cost, 4)
    
    # Store in campaign
    query("""
        UPDATE campaigns SET 
            validation_cost = %s, sending_cost = %s, total_cost = %s,
            credits_used = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (zb_cost, brevo_cost, total, validated, campaign_id))
    
    return {'validation_cost': zb_cost, 'sending_cost': brevo_cost, 'total_cost': total, 'credits_used': validated}

@app.route('/commercial/costs')
def cost_dashboard():
    """Cost tracking dashboard for all campaigns."""
    rates = get_cost_rates()
    
    # Overall stats
    total_validated = query_val("SELECT coalesce(sum(credits_used), 0) FROM campaigns") or 0
    total_sent = query_val("SELECT coalesce(sum(total_sent), 0) FROM campaigns") or 0
    total_cost = query_val("SELECT coalesce(sum(total_cost), 0) FROM campaigns") or 0
    total_zb_cost = query_val("SELECT coalesce(sum(validation_cost), 0) FROM campaigns") or 0
    total_brevo_cost = query_val("SELECT coalesce(sum(sending_cost), 0) FROM campaigns") or 0
    
    # Remaining free
    zb_free_used = min(total_validated, rates['zerobounce_free_credits'])
    zb_free_remaining = max(0, rates['zerobounce_free_credits'] - zb_free_used)
    brevo_used = min(total_sent, rates['brevo_monthly_included'])
    brevo_remaining = max(0, rates['brevo_monthly_included'] - brevo_used)
    
    # Per-campaign breakdown
    campaigns = query("""
        SELECT id, name, status, total_contacts, total_validated, total_sent,
               credits_used, validation_cost, sending_cost, total_cost, created_at
        FROM campaigns
        ORDER BY created_at DESC
    """)
    
    # Recent recipients with costs
    recent = query("""
        SELECT c.name as campaign_name, cr.email, cr.validation_status, 
               cr.send_status, cr.validation_cost, cr.sending_cost,
               co.first_name, co.last_name, comp.name as company_name
        FROM campaign_recipients cr
        JOIN campaigns c ON c.id = cr.campaign_id
        JOIN contacts co ON co.id = cr.contact_id
        JOIN companies comp ON comp.id = co.company_id
        ORDER BY cr.id DESC
        LIMIT 50
    """)
    
    return render_template('cost_dashboard.html', 
                          rates=rates, total_validated=total_validated, total_sent=total_sent,
                          total_cost=total_cost, total_zb_cost=total_zb_cost, 
                          total_brevo_cost=total_brevo_cost,
                          zb_free_remaining=zb_free_remaining, brevo_remaining=brevo_remaining,
                          campaigns=campaigns, recent=recent,
                          section='commercial', active_page='commercial_costs')

@app.route('/commercial/campaigns/<int:id>/cost')
def campaign_cost(id):
    """Show cost breakdown for a single campaign."""
    campaign = query_one("SELECT * FROM campaigns WHERE id=%s", (id,))
    if not campaign: flash('Campaign not found', 'error'); return redirect('/commercial/campaigns')
    
    # Calculate/refresh costs
    cost = calculate_campaign_cost(id)
    campaign = query_one("SELECT * FROM campaigns WHERE id=%s", (id,))
    
    # Per-recipient cost details
    recipients = query("""
        SELECT cr.*, co.first_name, co.last_name, comp.name as company_name
        FROM campaign_recipients cr
        JOIN contacts co ON co.id = cr.contact_id
        JOIN companies comp ON comp.id = co.company_id
        WHERE cr.campaign_id = %s
        ORDER BY cr.validation_cost DESC, cr.send_status
    """, (id,))
    
    return render_template('campaign_cost.html', campaign=campaign, 
                          recipients=recipients, section='commercial',
                          active_page='commercial_campaigns')

# ── Main ────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('CRM_PORT', 80))
    print(f'\n🚀 SimRobotics CRM running on http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)
