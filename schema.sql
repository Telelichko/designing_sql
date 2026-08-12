--
-- PostgreSQL database dump
--

\restrict eXBUgykxEX9JethhxBFUJCd7uj26MXrd5ZppYKwmP4iKT7qkofubanXx8cyqOaq

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: records; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.records (
    id text,
    name text,
    category text,
    city text,
    address text,
    rating text,
    reviews_count text,
    site text,
    phone text
);


ALTER TABLE public.records OWNER TO myuser;

--
-- Name: records uq_row; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.records
    ADD CONSTRAINT uq_row UNIQUE (id, name, category, city, address, rating, reviews_count, site, phone);


--
-- Name: ix_records_address; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_records_address ON public.records USING btree (address);


--
-- Name: ix_records_category; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_records_category ON public.records USING btree (category);


--
-- Name: ix_records_city; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_records_city ON public.records USING btree (city);


--
-- Name: ix_records_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_records_id ON public.records USING btree (id);


--
-- Name: ix_records_name; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_records_name ON public.records USING btree (name);


--
-- Name: ix_records_phone; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_records_phone ON public.records USING btree (phone);


--
-- Name: ix_records_rating; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_records_rating ON public.records USING btree (rating);


--
-- Name: ix_records_reviews_count; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_records_reviews_count ON public.records USING btree (reviews_count);


--
-- Name: ix_records_site; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX ix_records_site ON public.records USING btree (site);


--
-- PostgreSQL database dump complete
--

\unrestrict eXBUgykxEX9JethhxBFUJCd7uj26MXrd5ZppYKwmP4iKT7qkofubanXx8cyqOaq

