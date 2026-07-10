--
-- PostgreSQL database dump
--

\restrict 8i0Gj1eFfboyrz4LlhhfNeQoen8fAJASUn8RmAnlA1vuVuWQBqwJ7ifBdSeyWVX

-- Dumped from database version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.companies (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    sector character varying(100),
    region character varying(100),
    website text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    source_file character varying(255),
    business_type character varying(100)
);


--
-- Name: companies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.companies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- Name: contacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contacts (
    id integer NOT NULL,
    company_id integer,
    first_name character varying(100) NOT NULL,
    last_name character varying(100),
    role character varying(255),
    email character varying(255),
    phone character varying(50),
    linkedin_url text,
    needs_research boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    source_file character varying(255)
);


--
-- Name: contacts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contacts_id_seq OWNED BY public.contacts.id;


--
-- Name: interactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.interactions (
    id integer NOT NULL,
    contact_id integer,
    interaction_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    channel character varying(50),
    notes text,
    next_action text
);


--
-- Name: interactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.interactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: interactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.interactions_id_seq OWNED BY public.interactions.id;


--
-- Name: military_bases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.military_bases (
    id integer NOT NULL,
    base_name character varying(255) NOT NULL,
    branch character varying(100),
    state character varying(100),
    city character varying(100),
    country character varying(100) DEFAULT 'USA'::character varying,
    base_type character varying(100),
    command_name character varying(255),
    small_business_office text,
    contracting_office text,
    sb_office_email character varying(255),
    sb_office_phone character varying(100),
    website text,
    date_verified date,
    status character varying(50) DEFAULT 'Active'::character varying,
    opportunity_notes text,
    next_action text,
    notes text,
    priority boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: military_bases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.military_bases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: military_bases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.military_bases_id_seq OWNED BY public.military_bases.id;


--
-- Name: military_contacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.military_contacts (
    id integer NOT NULL,
    base_id integer,
    contact_name character varying(255),
    title character varying(255),
    email character varying(255),
    phone character varying(100),
    contact_role character varying(100) DEFAULT 'Small Business POC'::character varying,
    decision_maker boolean DEFAULT false,
    needs_followup boolean DEFAULT false,
    notes text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: military_contacts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.military_contacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: military_contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.military_contacts_id_seq OWNED BY public.military_contacts.id;


--
-- Name: military_opportunities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.military_opportunities (
    id integer NOT NULL,
    base_id integer,
    opportunity_name character varying(255) NOT NULL,
    solicitation_number character varying(100),
    contract_value numeric(15,2),
    phase character varying(100),
    estimated_award date,
    probability integer DEFAULT 0,
    service_type character varying(255),
    notes text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: military_opportunities_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.military_opportunities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: military_opportunities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.military_opportunities_id_seq OWNED BY public.military_opportunities.id;


--
-- Name: military_outreach; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.military_outreach (
    id integer NOT NULL,
    base_id integer,
    contact_id integer,
    capability_briefing_requested boolean DEFAULT false,
    outreach_date date,
    channel character varying(50),
    subject character varying(255),
    response text,
    briefing_scheduled date,
    follow_up_date date,
    status character varying(50) DEFAULT 'Not Contacted'::character varying,
    notes text,
    next_action text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: military_outreach_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.military_outreach_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: military_outreach_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.military_outreach_id_seq OWNED BY public.military_outreach.id;


--
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- Name: contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts ALTER COLUMN id SET DEFAULT nextval('public.contacts_id_seq'::regclass);


--
-- Name: interactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interactions ALTER COLUMN id SET DEFAULT nextval('public.interactions_id_seq'::regclass);


--
-- Name: military_bases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_bases ALTER COLUMN id SET DEFAULT nextval('public.military_bases_id_seq'::regclass);


--
-- Name: military_contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_contacts ALTER COLUMN id SET DEFAULT nextval('public.military_contacts_id_seq'::regclass);


--
-- Name: military_opportunities id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_opportunities ALTER COLUMN id SET DEFAULT nextval('public.military_opportunities_id_seq'::regclass);


--
-- Name: military_outreach id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_outreach ALTER COLUMN id SET DEFAULT nextval('public.military_outreach_id_seq'::regclass);


--
-- Name: companies companies_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_name_key UNIQUE (name);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- Name: interactions interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interactions
    ADD CONSTRAINT interactions_pkey PRIMARY KEY (id);


--
-- Name: military_bases military_bases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_bases
    ADD CONSTRAINT military_bases_pkey PRIMARY KEY (id);


--
-- Name: military_contacts military_contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_contacts
    ADD CONSTRAINT military_contacts_pkey PRIMARY KEY (id);


--
-- Name: military_opportunities military_opportunities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_opportunities
    ADD CONSTRAINT military_opportunities_pkey PRIMARY KEY (id);


--
-- Name: military_outreach military_outreach_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_outreach
    ADD CONSTRAINT military_outreach_pkey PRIMARY KEY (id);


--
-- Name: contacts contacts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: interactions interactions_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interactions
    ADD CONSTRAINT interactions_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id) ON DELETE CASCADE;


--
-- Name: military_contacts military_contacts_base_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_contacts
    ADD CONSTRAINT military_contacts_base_id_fkey FOREIGN KEY (base_id) REFERENCES public.military_bases(id) ON DELETE CASCADE;


--
-- Name: military_opportunities military_opportunities_base_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_opportunities
    ADD CONSTRAINT military_opportunities_base_id_fkey FOREIGN KEY (base_id) REFERENCES public.military_bases(id) ON DELETE CASCADE;


--
-- Name: military_outreach military_outreach_base_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_outreach
    ADD CONSTRAINT military_outreach_base_id_fkey FOREIGN KEY (base_id) REFERENCES public.military_bases(id) ON DELETE CASCADE;


--
-- Name: military_outreach military_outreach_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.military_outreach
    ADD CONSTRAINT military_outreach_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.military_contacts(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict 8i0Gj1eFfboyrz4LlhhfNeQoen8fAJASUn8RmAnlA1vuVuWQBqwJ7ifBdSeyWVX

