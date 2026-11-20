-- =====================================================================
--  GameVerse - ONE-STEP SETUP FOR pgAdmin4
-- ---------------------------------------------------------------------
--  Run this whole file in pgAdmin's Query Tool (F5) on a NEW, EMPTY
--  database (e.g. one named GameVerse). It contains:
--    Part 1: the group's Assignment 3 schema + data (gameverse_schema.sql,
--            with its COPY blocks converted to INSERTs, because pgAdmin
--            cannot run "COPY ... FROM stdin")
--    Part 2: sql/dev_backend_stub.sql (logins, functions, triggers)
-- =====================================================================

-- ============================ PART 1 =================================
--
-- PostgreSQL database dump
--


-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

-- Started on 2026-11-16 00:56:24

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
-- TOC entry 6 (class 2615 OID 16388)
-- Name: gameverse; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA gameverse;


ALTER SCHEMA gameverse OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 223 (class 1259 OID 17948)
-- Name: gametransactions; Type: TABLE; Schema: gameverse; Owner: postgres
--

CREATE TABLE gameverse.gametransactions (
    transactionid integer NOT NULL,
    walletid integer NOT NULL,
    transactiondate date,
    amount numeric(12,2),
    transactiontype character varying(50),
    recipient character varying(100),
    paymentmethod character varying(50),
    CONSTRAINT chk_txn_amount_nonzero CHECK ((amount <> (0)::numeric)),
    CONSTRAINT chk_txn_sign_matches_type CHECK (
CASE
    WHEN ((transactiontype)::text = 'TopUp'::text) THEN (amount > (0)::numeric)
    WHEN ((transactiontype)::text = ANY ((ARRAY['Cashout'::character varying, 'Purchase'::character varying])::text[])) THEN (amount < (0)::numeric)
    ELSE true
END)
);


ALTER TABLE gameverse.gametransactions OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 17913)
-- Name: gaminghubs; Type: TABLE; Schema: gameverse; Owner: postgres
--

CREATE TABLE gameverse.gaminghubs (
    hubid integer NOT NULL,
    hubname character varying(100) NOT NULL,
    location text,
    isactive boolean
);


ALTER TABLE gameverse.gaminghubs OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 17937)
-- Name: players; Type: TABLE; Schema: gameverse; Owner: postgres
--

CREATE TABLE gameverse.players (
    playerid integer NOT NULL,
    firstname character varying(100) NOT NULL,
    lastname character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    phone character varying(20),
    dateofbirth date,
    registrationdate date,
    isactive boolean,
    CONSTRAINT chk_player_min_age CHECK ((registrationdate >= ((dateofbirth + '13 years'::interval))::date)),
    CONSTRAINT chk_player_reg_not_future CHECK ((registrationdate <= CURRENT_DATE))
);


ALTER TABLE gameverse.players OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 17960)
-- Name: walletholders; Type: TABLE; Schema: gameverse; Owner: postgres
--

CREATE TABLE gameverse.walletholders (
    walletid integer NOT NULL,
    playerid integer NOT NULL,
    holderrole character varying(50),
    joindate date,
    depositamount numeric(12,2)
);


ALTER TABLE gameverse.walletholders OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 17977)
-- Name: walletreviews; Type: TABLE; Schema: gameverse; Owner: postgres
--

CREATE TABLE gameverse.walletreviews (
    reviewid integer NOT NULL,
    playerid integer NOT NULL,
    walletid integer NOT NULL,
    rating integer,
    reviewtext text,
    reviewdate date,
    isverified boolean,
    CONSTRAINT chk_review_date_not_future CHECK ((reviewdate <= CURRENT_DATE)),
    CONSTRAINT walletreviews_rating_check CHECK (((rating >= 1) AND (rating <= 5)))
);


ALTER TABLE gameverse.walletreviews OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 17922)
-- Name: wallets; Type: TABLE; Schema: gameverse; Owner: postgres
--

CREATE TABLE gameverse.wallets (
    walletid integer NOT NULL,
    wallettype character varying(100) NOT NULL,
    hubid integer NOT NULL,
    balance numeric(12,2),
    bonusrate numeric(5,2),
    walletdescription text,
    opendate date,
    minimumbalance numeric(12,2),
    isactive boolean,
    CONSTRAINT chk_wallet_balance_min CHECK ((balance >= minimumbalance)),
    CONSTRAINT chk_wallet_bonusrate CHECK (((bonusrate >= (0)::numeric) AND (bonusrate <= (5)::numeric))),
    CONSTRAINT chk_wallet_type CHECK (((wallettype)::text = ANY ((ARRAY['Standard'::character varying, 'Vault'::character varying, 'Guild'::character varying])::text[])))
);


ALTER TABLE gameverse.wallets OWNER TO postgres;

--
-- TOC entry 5058 (class 0 OID 17948)
-- Dependencies: 223
-- Data for Name: gametransactions; Type: TABLE DATA; Schema: gameverse; Owner: postgres
--

INSERT INTO gameverse.gametransactions (transactionid, walletid, transactiondate, amount, transactiontype, recipient, paymentmethod) VALUES
    ('8001', '2001', '2024-01-05', '1500.00', 'TopUp', 'Self', 'Hub Counter'),
    ('8002', '2001', '2024-01-10', '-250.00', 'Cashout', 'Self', 'Kiosk'),
    ('8003', '2002', '2024-01-15', '5000.00', 'TopUp', 'Self', 'App'),
    ('8004', '2003', '2024-01-18', '-2500.00', 'Purchase', 'Epic Skins Store', 'Bank Transfer'),
    ('8005', '2004', '2024-01-20', '800.00', 'TopUp', 'Self', 'Kiosk'),
    ('8006', '2001', '2024-01-22', '-500.00', 'Transfer', 'Wallet 2002', 'App'),
    ('8007', '2002', '2024-01-22', '500.00', 'Transfer', 'From Wallet 2001', 'App'),
    ('8008', '2005', '2024-01-25', '2000.00', 'TopUp', 'Self', 'Hub Counter'),
    ('8009', '2006', '2024-01-28', '-150.00', 'Cashout', 'Self', 'Kiosk'),
    ('8010', '2007', '2024-02-01', '10000.00', 'TopUp', 'Self', 'Bank Transfer'),
    ('8011', '2008', '2024-02-03', '-15000.00', 'Purchase', 'Titan Studios', 'App'),
    ('8012', '2004', '2024-02-05', '-300.00', 'Cashout', 'Self', 'Hub Counter'),
    ('8013', '2009', '2024-02-08', '500.00', 'TopUp', 'Self', 'Kiosk'),
    ('8014', '2010', '2024-02-10', '3000.00', 'TopUp', 'Self', 'App'),
    ('8015', '2011', '2024-02-12', '-1200.00', 'Purchase', 'Server Subscription', 'App'),
    ('8016', '2003', '2024-02-15', '8000.00', 'TopUp', 'Tournament Prize', 'Bank Transfer'),
    ('8017', '2012', '2024-02-18', '-5000.00', 'Transfer', 'Wallet 2013', 'App'),
    ('8018', '2013', '2024-02-18', '5000.00', 'Transfer', 'From Wallet 2012', 'App'),
    ('8019', '2002', '2024-02-20', '-1000.00', 'Cashout', 'Self', 'Hub Counter'),
    ('8020', '2014', '2024-02-22', '1500.00', 'TopUp', 'Self', 'Kiosk'),
    ('8021', '2015', '2024-02-25', '7500.00', 'TopUp', 'Self', 'App'),
    ('8022', '2001', '2024-02-28', '-180.00', 'Purchase', 'Battle Pass', 'App'),
    ('8023', '2006', '2024-03-01', '400.00', 'TopUp', 'Self', 'Hub Counter'),
    ('8024', '2007', '2024-03-05', '-2000.00', 'Cashout', 'Self', 'Hub Counter'),
    ('8025', '2011', '2024-03-08', '2500.00', 'TopUp', 'Self', 'App'),
    ('8026', '2004', '2024-03-10', '-450.00', 'Transfer', 'Wallet 2005', 'App'),
    ('8027', '2005', '2024-03-10', '450.00', 'Transfer', 'From Wallet 2004', 'App'),
    ('8028', '2008', '2024-03-12', '25000.00', 'TopUp', 'Sponsorship Revenue', 'Bank Transfer'),
    ('8029', '2014', '2024-03-15', '-800.00', 'Purchase', 'Gear Insurance', 'App'),
    ('8030', '2010', '2024-03-18', '-500.00', 'Cashout', 'Self', 'Kiosk');


--
-- TOC entry 5055 (class 0 OID 17913)
-- Dependencies: 220
-- Data for Name: gaminghubs; Type: TABLE DATA; Schema: gameverse; Owner: postgres
--

INSERT INTO gameverse.gaminghubs (hubid, hubname, location, isactive) VALUES
    ('1', 'Neon City Hub', 'Game Verse Plaza, Tokyo District', 't'),
    ('2', 'Starbase Hub', 'Starbase Arcade, Seoul District', 't'),
    ('3', 'Coral Bay Hub', 'Coral Bay Center, Miami District', 't'),
    ('4', 'Ironforge Hub', 'Ironforge Tower, Berlin District', 't'),
    ('5', 'Old Server Hub', 'Legacy Server Farm, Austin District', 'f');


--
-- TOC entry 5057 (class 0 OID 17937)
-- Dependencies: 222
-- Data for Name: players; Type: TABLE DATA; Schema: gameverse; Owner: postgres
--

INSERT INTO gameverse.players (playerid, firstname, lastname, email, phone, dateofbirth, registrationdate, isactive) VALUES
    ('3001', 'Alex', 'Chen', 'alex.chen@gameverse.com', '904-555-0201', '1998-03-15', '2022-01-10', 't'),
    ('3002', 'Bianca', 'Ruiz', 'bianca.ruiz@gameverse.com', '904-555-0202', '2000-07-22', '2022-02-15', 't'),
    ('3003', 'Carlos', 'Nguyen', 'carlos.nguyen@gameverse.com', '904-555-0203', '1995-11-30', '2021-11-05', 't'),
    ('3004', 'Dana', 'Kim', 'dana.kim@gameverse.com', '904-555-0204', '1999-05-18', '2023-03-01', 't'),
    ('3005', 'Ethan', 'Park', 'ethan.park@gameverse.com', '904-555-0205', '1997-09-12', '2023-01-08', 't'),
    ('3006', 'Farah', 'Ali', 'farah.ali@gameverse.com', '904-555-0206', '2001-12-25', '2023-06-15', 't'),
    ('3007', 'Gavin', 'Lopez', 'gavin.lopez@gameverse.com', '904-555-0207', '1993-04-08', '2022-05-20', 't'),
    ('3008', 'Hana', 'Suzuki', 'hana.suzuki@gameverse.com', '904-555-0208', '1990-08-14', '2021-08-25', 't'),
    ('3009', 'Ivan', 'Petrov', 'ivan.petrov@gameverse.com', '904-555-0209', '2002-01-30', '2023-09-10', 't'),
    ('3010', 'Jade', 'Wong', 'jade.wong@gameverse.com', '904-555-0210', '1996-06-20', '2022-11-28', 't'),
    ('3011', 'Kevin', 'Osei', 'kevin.osei@gameverse.com', '904-555-0211', '1994-10-05', '2023-02-22', 't'),
    ('3012', 'Lena', 'Novak', 'lena.novak@gameverse.com', '904-555-0212', '1992-03-17', '2022-07-15', 't'),
    ('3013', 'Marco', 'Rossi', 'marco.rossi@gameverse.com', '904-555-0213', '1998-11-28', '2023-04-05', 't'),
    ('3014', 'Nadia', 'Haddad', 'nadia.haddad@gameverse.com', '904-555-0214', '1997-02-14', '2023-08-20', 't'),
    ('3015', 'Omar', 'Farouk', 'omar.farouk@gameverse.com', '904-555-0215', '1989-07-09', '2022-10-01', 't');


--
-- TOC entry 5059 (class 0 OID 17960)
-- Dependencies: 224
-- Data for Name: walletholders; Type: TABLE DATA; Schema: gameverse; Owner: postgres
--

INSERT INTO gameverse.walletholders (walletid, playerid, holderrole, joindate, depositamount) VALUES
    ('2001', '3001', 'Owner', '2022-01-15', '1000.00'),
    ('2002', '3001', 'Owner', '2022-02-20', '10000.00'),
    ('2003', '3003', 'Owner', '2021-11-10', '45000.00'),
    ('2004', '3004', 'Owner', '2023-03-05', '2500.00'),
    ('2005', '3005', 'Owner', '2023-01-12', '6000.00'),
    ('2006', '3006', 'Owner', '2023-06-18', '1000.00'),
    ('2007', '3007', 'Owner', '2022-05-22', '20000.00'),
    ('2008', '3008', 'Owner', '2021-08-30', '50000.00'),
    ('2009', '3009', 'Owner', '2023-09-14', '500.00'),
    ('2010', '3010', 'Owner', '2022-12-01', '9000.00'),
    ('2011', '3011', 'Owner', '2023-02-28', '5000.00'),
    ('2012', '3012', 'Owner', '2022-07-19', '25000.00'),
    ('2013', '3013', 'Owner', '2023-04-10', '5000.00'),
    ('2014', '3014', 'Owner', '2023-08-25', '2000.00'),
    ('2015', '3015', 'Owner', '2022-10-05', '15000.00'),
    ('2002', '3002', 'Co-Owner', '2022-03-01', '5000.00'),
    ('2007', '3002', 'Co-Owner', '2022-06-15', '5000.00'),
    ('2012', '3003', 'Member', '2022-08-01', '0.00'),
    ('2004', '3005', 'Co-Owner', '2023-04-20', '1000.00'),
    ('2011', '3010', 'Co-Owner', '2023-03-15', '1000.00');


--
-- TOC entry 5060 (class 0 OID 17977)
-- Dependencies: 225
-- Data for Name: walletreviews; Type: TABLE DATA; Schema: gameverse; Owner: postgres
--

INSERT INTO gameverse.walletreviews (reviewid, playerid, walletid, rating, reviewtext, reviewdate, isverified) VALUES
    ('6001', '3001', '2001', '5', 'Excellent standard wallet with no hidden fees. Very satisfied with the service.', '2024-02-01', 't'),
    ('6002', '3002', '2002', '4', 'Good bonus rate on the vault. The app could be improved.', '2024-02-05', 't'),
    ('6003', '3003', '2003', '5', 'Perfect for my guild needs. Transaction limits are reasonable and fees are low.', '2024-02-10', 't'),
    ('6004', '3004', '2004', '5', 'Great support at the Coral Bay hub. Quick wallet setup.', '2024-03-08', 't'),
    ('6005', '3005', '2005', '3', 'Average vault wallet. Bonus rate could be better.', '2024-02-15', 't'),
    ('6006', '3006', '2006', '5', 'Perfect rookie wallet! No maintenance fees and easy to use app.', '2024-07-20', 't'),
    ('6007', '3007', '2007', '4', 'High bonus rates are great, but minimum balance requirement is steep.', '2024-06-10', 't'),
    ('6008', '3008', '2008', '5', 'Excellent guild treasury experience. Transfers are fast and reliable.', '2024-03-15', 't'),
    ('6009', '3009', '2009', '2', 'Had some issues with kiosk cashouts. Support was slow to respond.', '2024-10-01', 'f'),
    ('6010', '3010', '2010', '4', 'Solid vault wallet with decent rates. Hub staff is very helpful.', '2024-01-20', 't'),
    ('6011', '3011', '2011', '5', 'Love the premium standard wallet features. Free perks and overdraft protection.', '2024-03-25', 't'),
    ('6012', '3001', '2002', '5', 'Best vault wallet I have had. Bonus compounds monthly.', '2024-03-01', 't'),
    ('6013', '3013', '2013', '4', 'Good squad savings option. Easy to track goals.', '2024-05-15', 't'),
    ('6014', '3014', '2014', '3', 'Standard wallet. Nothing special but gets the job done.', '2024-09-10', 't'),
    ('6015', '3015', '2015', '5', 'Fantastic high-bonus vault! Rates beat all competitors.', '2024-11-05', 't');


--
-- TOC entry 5056 (class 0 OID 17922)
-- Dependencies: 221
-- Data for Name: wallets; Type: TABLE DATA; Schema: gameverse; Owner: postgres
--

INSERT INTO gameverse.wallets (walletid, wallettype, hubid, balance, bonusrate, walletdescription, opendate, minimumbalance, isactive) VALUES
    ('2001', 'Standard', '1', '2500.00', '0.10', 'Basic wallet with no monthly fees', '2022-01-15', '100.00', 't'),
    ('2002', 'Vault', '1', '15000.00', '2.50', 'High-yield vault for saving in-game currency', '2022-02-20', '500.00', 't'),
    ('2003', 'Guild', '2', '50000.00', '1.75', 'Guild treasury wallet with transaction limits', '2021-11-10', '1000.00', 't'),
    ('2004', 'Standard', '3', '3200.00', '0.10', 'Basic wallet', '2023-03-05', '100.00', 't'),
    ('2005', 'Vault', '2', '8500.00', '2.50', 'Regular vault wallet', '2023-01-12', '500.00', 't'),
    ('2006', 'Standard', '1', '1200.00', '0.10', 'Rookie player wallet', '2023-06-18', '50.00', 't'),
    ('2007', 'Vault', '3', '25000.00', '3.00', 'Premium vault wallet', '2022-05-22', '1000.00', 't'),
    ('2008', 'Guild', '4', '75000.00', '1.50', 'Elite guild treasury', '2021-08-30', '2000.00', 't'),
    ('2009', 'Standard', '2', '450.00', '0.10', 'Basic starter wallet', '2023-09-14', '100.00', 't'),
    ('2010', 'Vault', '4', '12000.00', '2.25', 'Standard vault wallet', '2022-12-01', '500.00', 't'),
    ('2011', 'Standard', '3', '5600.00', '0.10', 'Premium standard wallet', '2023-02-28', '500.00', 't'),
    ('2012', 'Guild', '1', '32000.00', '1.75', 'Small guild wallet', '2022-07-19', '1000.00', 't'),
    ('2013', 'Vault', '2', '6800.00', '2.50', 'Squad savings wallet', '2023-04-10', '500.00', 't'),
    ('2014', 'Standard', '4', '2100.00', '0.10', 'Basic wallet', '2023-08-25', '100.00', 't'),
    ('2015', 'Vault', '1', '18500.00', '2.75', 'High-interest vault wallet', '2022-10-05', '1000.00', 't');


--
-- TOC entry 4894 (class 2606 OID 17954)
-- Name: gametransactions gametransactions_pkey; Type: CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.gametransactions
    ADD CONSTRAINT gametransactions_pkey PRIMARY KEY (transactionid);


--
-- TOC entry 4886 (class 2606 OID 17921)
-- Name: gaminghubs gaminghubs_pkey; Type: CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.gaminghubs
    ADD CONSTRAINT gaminghubs_pkey PRIMARY KEY (hubid);


--
-- TOC entry 4890 (class 2606 OID 17947)
-- Name: players players_email_key; Type: CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.players
    ADD CONSTRAINT players_email_key UNIQUE (email);


--
-- TOC entry 4892 (class 2606 OID 17945)
-- Name: players players_pkey; Type: CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.players
    ADD CONSTRAINT players_pkey PRIMARY KEY (playerid);


--
-- TOC entry 4899 (class 2606 OID 18015)
-- Name: walletreviews uq_review_player_wallet; Type: CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.walletreviews
    ADD CONSTRAINT uq_review_player_wallet UNIQUE (playerid, walletid);


--
-- TOC entry 4897 (class 2606 OID 17966)
-- Name: walletholders walletholders_pkey; Type: CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.walletholders
    ADD CONSTRAINT walletholders_pkey PRIMARY KEY (walletid, playerid);


--
-- TOC entry 4901 (class 2606 OID 17987)
-- Name: walletreviews walletreviews_pkey; Type: CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.walletreviews
    ADD CONSTRAINT walletreviews_pkey PRIMARY KEY (reviewid);


--
-- TOC entry 4888 (class 2606 OID 17931)
-- Name: wallets wallets_pkey; Type: CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.wallets
    ADD CONSTRAINT wallets_pkey PRIMARY KEY (walletid);


--
-- TOC entry 4895 (class 1259 OID 18018)
-- Name: uq_one_owner_per_wallet; Type: INDEX; Schema: gameverse; Owner: postgres
--

CREATE UNIQUE INDEX uq_one_owner_per_wallet ON gameverse.walletholders USING btree (walletid) WHERE ((holderrole)::text = 'Owner'::text);


--
-- TOC entry 4904 (class 2606 OID 18003)
-- Name: walletholders fk_holder_player; Type: FK CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.walletholders
    ADD CONSTRAINT fk_holder_player FOREIGN KEY (playerid) REFERENCES gameverse.players(playerid) ON DELETE RESTRICT;


--
-- TOC entry 4905 (class 2606 OID 17998)
-- Name: walletholders fk_holder_wallet; Type: FK CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.walletholders
    ADD CONSTRAINT fk_holder_wallet FOREIGN KEY (walletid) REFERENCES gameverse.wallets(walletid) ON DELETE CASCADE;


--
-- TOC entry 4903 (class 2606 OID 17955)
-- Name: gametransactions gametransactions_walletid_fkey; Type: FK CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.gametransactions
    ADD CONSTRAINT gametransactions_walletid_fkey FOREIGN KEY (walletid) REFERENCES gameverse.wallets(walletid);


--
-- TOC entry 4906 (class 2606 OID 17988)
-- Name: walletreviews walletreviews_playerid_fkey; Type: FK CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.walletreviews
    ADD CONSTRAINT walletreviews_playerid_fkey FOREIGN KEY (playerid) REFERENCES gameverse.players(playerid);


--
-- TOC entry 4907 (class 2606 OID 17993)
-- Name: walletreviews walletreviews_walletid_fkey; Type: FK CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.walletreviews
    ADD CONSTRAINT walletreviews_walletid_fkey FOREIGN KEY (walletid) REFERENCES gameverse.wallets(walletid);


--
-- TOC entry 4902 (class 2606 OID 17932)
-- Name: wallets wallets_hubid_fkey; Type: FK CONSTRAINT; Schema: gameverse; Owner: postgres
--

ALTER TABLE ONLY gameverse.wallets
    ADD CONSTRAINT wallets_hubid_fkey FOREIGN KEY (hubid) REFERENCES gameverse.gaminghubs(hubid);


-- Completed on 2026-11-16 00:56:25

--
-- PostgreSQL database dump complete
--



-- ============================ PART 2 =================================
-- =====================================================================
--  GameVerse - DEV BACKEND STUB (frontend branch only)
-- ---------------------------------------------------------------------
--  This script exists so the frontend can be run and tested on its own
--  before it is merged with the backend branch. When the branches are
--  combined, the backend branch's SQL script REPLACES this file.
--
--  Run top-to-bottom in pgAdmin4 (or psql) on a database that already
--  has the Assignment 2/3 GameVerse schema + data loaded.
--
--  What it adds:
--    * ID defaults (sequences) so new rows can be inserted
--    * Login support: players.passwordhash + admins table (pgcrypto)
--    * linkedtxnid on gametransactions (transfer legs / reversals)
--    * Stored functions: performTransaction, transferFunds,
--      getWalletSummary, checkSufficientBalance, getLowBalanceAlerts
--    * Triggers: AFTER INSERT balance update, BEFORE INSERT inactive check
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
SET search_path TO gameverse, public;

-- ---------------------------------------------------------------------
-- 1. ID sequences (the Assignment 2 tables have no defaults)
-- ---------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS gaminghubs_hubid_seq       OWNED BY gaminghubs.hubid;
CREATE SEQUENCE IF NOT EXISTS wallets_walletid_seq       OWNED BY wallets.walletid;
CREATE SEQUENCE IF NOT EXISTS players_playerid_seq       OWNED BY players.playerid;
CREATE SEQUENCE IF NOT EXISTS gametransactions_txnid_seq OWNED BY gametransactions.transactionid;
CREATE SEQUENCE IF NOT EXISTS walletreviews_reviewid_seq OWNED BY walletreviews.reviewid;

SELECT setval('gaminghubs_hubid_seq',       (SELECT COALESCE(MAX(hubid), 0)         FROM gaminghubs) + 1, false);
SELECT setval('wallets_walletid_seq',       (SELECT COALESCE(MAX(walletid), 2000)   FROM wallets) + 1, false);
SELECT setval('players_playerid_seq',       (SELECT COALESCE(MAX(playerid), 3000)   FROM players) + 1, false);
SELECT setval('gametransactions_txnid_seq', (SELECT COALESCE(MAX(transactionid), 8000) FROM gametransactions) + 1, false);
SELECT setval('walletreviews_reviewid_seq', (SELECT COALESCE(MAX(reviewid), 6000)   FROM walletreviews) + 1, false);

ALTER TABLE gaminghubs       ALTER COLUMN hubid         SET DEFAULT nextval('gaminghubs_hubid_seq');
ALTER TABLE wallets          ALTER COLUMN walletid      SET DEFAULT nextval('wallets_walletid_seq');
ALTER TABLE players          ALTER COLUMN playerid      SET DEFAULT nextval('players_playerid_seq');
ALTER TABLE gametransactions ALTER COLUMN transactionid SET DEFAULT nextval('gametransactions_txnid_seq');
ALTER TABLE walletreviews    ALTER COLUMN reviewid      SET DEFAULT nextval('walletreviews_reviewid_seq');

ALTER TABLE gametransactions ALTER COLUMN transactiondate SET DEFAULT CURRENT_DATE;
ALTER TABLE walletreviews    ALTER COLUMN reviewdate      SET DEFAULT CURRENT_DATE;
ALTER TABLE walletreviews    ALTER COLUMN isverified      SET DEFAULT FALSE;
ALTER TABLE players          ALTER COLUMN registrationdate SET DEFAULT CURRENT_DATE;
ALTER TABLE players          ALTER COLUMN isactive        SET DEFAULT TRUE;
ALTER TABLE gaminghubs       ALTER COLUMN isactive        SET DEFAULT TRUE;
ALTER TABLE wallets          ALTER COLUMN isactive        SET DEFAULT TRUE;
ALTER TABLE wallets          ALTER COLUMN opendate        SET DEFAULT CURRENT_DATE;

-- ---------------------------------------------------------------------
-- 2. Login support
-- ---------------------------------------------------------------------
ALTER TABLE players ADD COLUMN IF NOT EXISTS passwordhash text;

CREATE TABLE IF NOT EXISTS admins (
    adminid      serial PRIMARY KEY,
    username     varchar(50) NOT NULL UNIQUE,
    passwordhash text        NOT NULL
);

-- Test credentials (documented in README_FRONTEND.md)
--   admin  / Admin@123
--   every seeded player / player123
INSERT INTO admins (username, passwordhash)
VALUES ('admin', crypt('Admin@123', gen_salt('bf')))
ON CONFLICT (username) DO NOTHING;

UPDATE players SET passwordhash = crypt('player123', gen_salt('bf'))
WHERE passwordhash IS NULL;

-- ---------------------------------------------------------------------
-- 3. Transfer / reversal linking
-- ---------------------------------------------------------------------
ALTER TABLE gametransactions ADD COLUMN IF NOT EXISTS linkedtxnid integer
    REFERENCES gametransactions(transactionid);

-- Link the existing Assignment 2 transfer pairs (8006/8007, 8017/8018, 8026/8027)
UPDATE gametransactions o SET linkedtxnid = i.transactionid
FROM gametransactions i
WHERE o.transactiontype = 'Transfer' AND i.transactiontype = 'Transfer'
  AND o.amount < 0 AND i.amount = -o.amount
  AND i.transactiondate = o.transactiondate
  AND i.recipient = 'From Wallet ' || o.walletid
  AND o.recipient = 'Wallet ' || i.walletid
  AND o.linkedtxnid IS NULL;
UPDATE gametransactions i SET linkedtxnid = o.transactionid
FROM gametransactions o
WHERE o.linkedtxnid = i.transactionid AND i.linkedtxnid IS NULL;

-- ---------------------------------------------------------------------
-- 4. Helper: money formatting used in error messages ("2,400.00")
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fmt_money(p numeric) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT to_char(p, 'FM999,999,999,990.00');
$$;

-- ---------------------------------------------------------------------
-- 5. checkSufficientBalance(walletID, requestedAmount) -> boolean
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION checkSufficientBalance(p_walletid integer, p_amount numeric)
RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE
    v_balance numeric; v_min numeric;
BEGIN
    SELECT balance, minimumbalance INTO v_balance, v_min
    FROM wallets WHERE walletid = p_walletid;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Wallet % does not exist.', p_walletid;
    END IF;
    RETURN (v_balance - p_amount) >= v_min;
END;
$$;

-- Internal helper that raises the standard "Insufficient funds" message
CREATE OR REPLACE FUNCTION assert_sufficient_balance(p_walletid integer, p_amount numeric)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
    v_balance numeric; v_min numeric;
BEGIN
    IF NOT checkSufficientBalance(p_walletid, p_amount) THEN
        SELECT balance, minimumbalance INTO v_balance, v_min FROM wallets WHERE walletid = p_walletid;
        RAISE EXCEPTION 'Insufficient funds. Spendable balance: % (balance %, minimum %)',
            fmt_money(GREATEST(v_balance - v_min, 0)), fmt_money(v_balance), fmt_money(v_min);
    END IF;
END;
$$;

-- ---------------------------------------------------------------------
-- 6. performTransaction(walletID, amount, type, paymentMethod, recipient)
--    amount is passed POSITIVE; sign is applied here. Not for Transfer.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION performTransaction(
    p_walletid integer, p_amount numeric, p_type varchar,
    p_method varchar, p_recipient varchar)
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE
    v_id integer; v_signed numeric;
BEGIN
    IF p_amount IS NULL OR p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be greater than zero.';
    END IF;
    IF p_type = 'Transfer' THEN
        RAISE EXCEPTION 'Use transferFunds for transfers.';
    ELSIF p_type NOT IN ('TopUp', 'Cashout', 'Purchase') THEN
        RAISE EXCEPTION 'Unknown transaction type: %', p_type;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM wallets WHERE walletid = p_walletid) THEN
        RAISE EXCEPTION 'Wallet % does not exist.', p_walletid;
    END IF;

    IF p_type = 'TopUp' THEN
        v_signed := p_amount;
    ELSE
        PERFORM assert_sufficient_balance(p_walletid, p_amount);
        v_signed := -p_amount;
    END IF;

    INSERT INTO gametransactions (walletid, transactiondate, amount, transactiontype, recipient, paymentmethod)
    VALUES (p_walletid, CURRENT_DATE, v_signed, p_type, COALESCE(NULLIF(p_recipient, ''), 'Self'), p_method)
    RETURNING transactionid INTO v_id;
    RETURN v_id;
END;
$$;

-- ---------------------------------------------------------------------
-- 7. transferFunds(fromWalletID, toWalletID, amount, paymentMethod)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION transferFunds(
    p_from integer, p_to integer, p_amount numeric, p_method varchar)
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE
    v_out integer; v_in integer;
BEGIN
    IF p_amount IS NULL OR p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be greater than zero.';
    END IF;
    IF p_from = p_to THEN
        RAISE EXCEPTION 'Source and destination wallets must be different.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM wallets WHERE walletid = p_to) THEN
        RAISE EXCEPTION 'Destination wallet % does not exist.', p_to;
    END IF;
    PERFORM assert_sufficient_balance(p_from, p_amount);

    INSERT INTO gametransactions (walletid, transactiondate, amount, transactiontype, recipient, paymentmethod)
    VALUES (p_from, CURRENT_DATE, -p_amount, 'Transfer', 'Wallet ' || p_to, p_method)
    RETURNING transactionid INTO v_out;

    INSERT INTO gametransactions (walletid, transactiondate, amount, transactiontype, recipient, paymentmethod, linkedtxnid)
    VALUES (p_to, CURRENT_DATE, p_amount, 'Transfer', 'From Wallet ' || p_from, p_method, v_out)
    RETURNING transactionid INTO v_in;

    UPDATE gametransactions SET linkedtxnid = v_in WHERE transactionid = v_out;
    RETURN v_out;
END;
$$;

-- ---------------------------------------------------------------------
-- 8. getWalletSummary(walletID)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION getWalletSummary(p_walletid integer)
RETURNS TABLE (balance numeric, total_topups numeric, total_cashouts numeric,
               total_purchases numeric, transfers_in numeric, transfers_out numeric,
               transaction_count bigint)
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM wallets w WHERE w.walletid = p_walletid) THEN
        RAISE EXCEPTION 'Wallet % does not exist.', p_walletid;
    END IF;
    RETURN QUERY
    SELECT w.balance,
           COALESCE(SUM(t.amount) FILTER (WHERE t.transactiontype = 'TopUp'), 0),
           COALESCE(-SUM(t.amount) FILTER (WHERE t.transactiontype = 'Cashout'), 0),
           COALESCE(-SUM(t.amount) FILTER (WHERE t.transactiontype = 'Purchase'), 0),
           COALESCE(SUM(t.amount) FILTER (WHERE t.transactiontype = 'Transfer' AND t.amount > 0), 0),
           COALESCE(-SUM(t.amount) FILTER (WHERE t.transactiontype = 'Transfer' AND t.amount < 0), 0),
           COUNT(t.transactionid)
    FROM wallets w
    LEFT JOIN gametransactions t ON t.walletid = w.walletid
    WHERE w.walletid = p_walletid
    GROUP BY w.balance;
END;
$$;

-- ---------------------------------------------------------------------
-- 9. getLowBalanceAlerts(threshold)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION getLowBalanceAlerts(p_threshold numeric)
RETURNS TABLE (walletid integer, wallettype varchar, balance numeric,
               minimumbalance numeric, hubname varchar)
LANGUAGE sql AS $$
    SELECT w.walletid, w.wallettype, w.balance, w.minimumbalance, h.hubname
    FROM wallets w JOIN gaminghubs h ON h.hubid = w.hubid
    WHERE w.isactive AND w.balance < p_threshold
    ORDER BY w.balance;
$$;

-- ---------------------------------------------------------------------
-- 10. Triggers
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_reject_inactive_wallet() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM wallets WHERE walletid = NEW.walletid AND isactive) THEN
        RAISE EXCEPTION 'Wallet % is inactive. Transactions are not allowed.', NEW.walletid;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION trg_apply_balance() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE wallets SET balance = balance + NEW.amount WHERE walletid = NEW.walletid;
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_txn_reject_inactive ON gametransactions;
CREATE TRIGGER trg_txn_reject_inactive
    BEFORE INSERT ON gametransactions
    FOR EACH ROW EXECUTE FUNCTION trg_reject_inactive_wallet();

DROP TRIGGER IF EXISTS trg_txn_apply_balance ON gametransactions;
CREATE TRIGGER trg_txn_apply_balance
    AFTER INSERT ON gametransactions
    FOR EACH ROW EXECUTE FUNCTION trg_apply_balance();
