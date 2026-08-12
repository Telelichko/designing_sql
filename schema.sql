--
-- PostgreSQL database dump
--

\restrict 3Sb2RNY8V4v1hCM9sOyszmHahFcBzgxCC2t6AXezddBwe743DlzVTwlA9nsPKcR

-- Dumped from database version 16.14
-- Dumped by pg_dump version 16.14

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

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: myuser
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO myuser;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: myuser
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: companies; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.companies (
    id character varying(50) NOT NULL,
    name character varying(255),
    category character varying(100),
    city character varying(100),
    address character varying(255),
    rating numeric(5,2),
    reviews_count integer,
    site character varying(255),
    phone character varying(50),
    email character varying(255)
);


ALTER TABLE public.companies OWNER TO myuser;

--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: ix_companies_category; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_companies_category ON public.companies USING btree (category);


--
-- Name: ix_companies_city; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_companies_city ON public.companies USING btree (city);


--
-- Name: ix_companies_email; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_companies_email ON public.companies USING btree (email);


--
-- Name: ix_companies_rating; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_companies_rating ON public.companies USING btree (rating);


--
-- Name: ix_companies_reviews_count; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_companies_reviews_count ON public.companies USING btree (reviews_count);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: myuser
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict 3Sb2RNY8V4v1hCM9sOyszmHahFcBzgxCC2t6AXezddBwe743DlzVTwlA9nsPKcR

