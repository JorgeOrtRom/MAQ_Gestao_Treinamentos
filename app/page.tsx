'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { createClient } from '@supabase/supabase-js';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid
} from 'recharts';
import { 
  Users, Award, BookOpen, CheckCircle, AlertTriangle, FileText, Upload, Save, Plus, Search, Printer, Layers, ExternalLink, Trash2, LogOut, Lock, Mail, UserPlus, Shield, Calendar as CalendarIcon, Edit3, X, Activity, TrendingUp, CheckSquare, Building, UserCheck, Clock
} from 'lucide-react';

const SUPABASE_URL = 'https://qpmgzztaduetfrjcvswo.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_tGyuT8NnOb67vrbcC8dTFA_wYrn2hkP';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export default function EnterpriseDashboard() {
  const [session, setSession] = useState<any>(null);
  const [email, setEmail] = useState('admin@attendambiental.com.br');
  const [password, setPassword] = useState('admin123');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState('');

  const [activeTab, setActiveTab] = useState('relatorio_curso');
  const [selectedAno, setSelectedAno] = useState<number>(new Date().getFullYear());
  const [colaboradores, setColaboradores] = useState<any[]>([]);
  const [treinamentos, setTreinamentos] = useState<any[]>([]);
  const [registros, setRegistros] = useState<any[]>([]);
  const [matrizLnt, setMatrizLnt] = useState<any[]>([]);
  const [selectedColab, setSelectedColab] = useState<string>('');
  
  const [selectedTreinamentoRelatorio, setSelectedTreinamentoRelatorio] = useState<string>('');
  const [colabCertificado, setColabCertificado] = useState<any | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [searchColabTab, setSearchColabTab] = useState<string>('');

  const [isOutroCargo, setIsOutroCargo] = useState<boolean>(false);
  const [cargoManual, setCargoManual] = useState<string>('');

  const [novoColab, setNovoColab] = useState({ nome: '', cargo: '', departamento: '', gestor: '' });
  const [editingColabId, setEditingColabId] = useState<string | null>(null);
  const [editColabForm, setEditColabForm] = useState({ nome: '', cargo: '', departamento: '', gestor: '' });

  const [novoTreino, setNovoTreino] = useState({ nome_curso: '', carga_horaria: 1, frequencia: 'ANUAL', classificacao: 'Exigência da função', aplicador_padrao: '' });
  const [novaMatriz, setNovaMatriz] = useState({ cargo: '', treinamento_id: '' });
  
  const [novoUsuario, setNovoUsuario] = useState({ email: '', password: '' });
  const [userSuccess, setUserSuccess] = useState('');

  // ESTADO DO CALENDÁRIO / AGENDAMENTO PREVISTO
  const [datasPrevistas, setDatasPrevistas] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) fetchInitialData();
      else setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) fetchInitialData();
    });

    return () => subscription.unsubscribe();
  }, []);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError('');
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) setAuthError('Falha na autenticação: ' + error.message);
    setAuthLoading(false);
  }

  async function handleLogout() {
    await supabase.auth.signOut();
    setSession(null);
  }

  async function handleCreateUser(e: React.FormEvent) {
    e.preventDefault();
    setUserSuccess('');
    if (!novoUsuario.email || !novoUsuario.password) return alert('Preencha e-mail e senha!');
    const { data, error } = await supabase.auth.signUp({ email: novoUsuario.email, password: novoUsuario.password });
    if (error) alert('Erro ao criar utilizador: ' + error.message);
    else {
      setUserSuccess(`Utilizador ${novoUsuario.email} criado com sucesso!`);
      setNovoUsuario({ email: '', password: '' });
    }
  }

  async function fetchInitialData() {
    const { data: colabs } = await supabase.from('colaboradores').select('*').order('nome');
    const { data: treinos } = await supabase.from('treinamentos').select('*').order('nome_curso');
    const { data: regs } = await supabase.from('registros').select('*, colaboradores(nome, departamento, cargo), treinamentos(nome_curso, carga_horaria, classificacao)');
    const { data: matriz } = await supabase.from('matriz_cargo_treinamento').select('*, treinamentos(nome_curso, carga_horaria)');

    if (colabs) setColaboradores(colabs);
    if (treinos) {
      setTreinamentos(treinos);
      if (treinos.length > 0 && !selectedTreinamentoRelatorio) setSelectedTreinamentoRelatorio(String(treinos[0].id));
    }
    if (regs) setRegistros(regs);
    if (matriz) setMatrizLnt(matriz);

    if (colabs && colabs.length > 0 && !selectedColab) setSelectedColab(String(colabs[0].id));
    setLoading(false);
  }

  const cargosUnicos = Array.from(new Set([
    ...colaboradores.map(c => c.cargo),
    ...matrizLnt.map(m => m.cargo)
  ].filter(c => c && typeof c === 'string' && c.trim() !== ''))).sort();

  const registrosAno = useMemo(() => {
    const idsColabsValidos = new Set(colaboradores.map(c => String(c.id)));
    const idsTreinosValidos = new Set(treinamentos.map(t => String(t.id)));

    return registros.filter(r => {
      if (!r.data_realizacao) return false;
      const pertenceAoAno = String(r.data_realizacao).startsWith(String(selectedAno));
      const colabExiste = idsColabsValidos.has(String(r.colaborador_id));
      const treinoExiste = idsTreinosValidos.has(String(r.treinamento_id));
      return pertenceAoAno && colabExiste && treinoExiste;
    });
  }, [registros, selectedAno, colaboradores, treinamentos]);

  const totalHoras = useMemo(() => {
    return registrosAno.reduce((acc, r) => acc + (Number(r.treinamentos?.carga_horaria) || 0), 0);
  }, [registrosAno]);

  const totalConcluidos = registrosAno.length;

  const complianceTaxa = useMemo(() => {
    if (!matrizLnt.length) return 0;
    return Math.min(100, Math.round((totalConcluidos / matrizLnt.length) * 100));
  }, [totalConcluidos, matrizLnt.length]);

  const pendenciasTotais = useMemo(() => {
    return Math.max(0, matrizLnt.length - totalConcluidos);
  }, [matrizLnt.length, totalConcluidos]);

  const cargosComLnt = useMemo(() => new Set(matrizLnt.map(m => m.cargo)), [matrizLnt]);
  
  const pessoasMapeadas = useMemo(() => {
    return colaboradores.filter(c => cargosComLnt.has(c.cargo));
  }, [colaboradores, cargosComLnt]);

  const mediaHorasPorPessoa = useMemo(() => {
    if (!pessoasMapeadas.length) return 0;
    return (totalHoras / pessoasMapeadas.length).toFixed(1);
  }, [totalHoras, pessoasMapeadas.length]);

  const dadosPorDepartamento = useMemo(() => {
    const mapa: { [key: string]: { setor: string; concluidos: number } } = {};
    
    colaboradores.forEach(c => {
      const depto = c.departamento || 'Sem Setor';
      if (!mapa[depto]) mapa[depto] = { setor: depto, concluidos: 0 };
    });

    registrosAno.forEach(r => {
      const colab = colaboradores.find(c => String(c.id) === String(r.colaborador_id));
      const depto = colab?.departamento || 'Sem Setor';
      if (!mapa[depto]) mapa[depto] = { setor: depto, concluidos: 0 };
      mapa[depto].concluidos += 1;
    });

    return Object.values(mapa).sort((a, b) => b.concluidos - a.concluidos);
  }, [colaboradores, registrosAno]);

  const dadosGraficoTreinamentos = useMemo(() => {
    return treinamentos.map(t => {
      const nomeCompleto = t.nome_curso || '';
      const codigoAbreviado = nomeCompleto.length > 20 ? `${nomeCompleto.substring(0, 18)}...` : nomeCompleto;
      return {
        id: t.id,
        nomeAbreviado: codigoAbreviado,
        nomeCompleto: nomeCompleto,
        carga_horaria: Number(t.carga_horaria) || 0
      };
    });
  }, [treinamentos]);

  const statusData = useMemo(() => [
    { name: '🟢 Concluídos', value: totalConcluidos },
    { name: '🔴 Pendentes LNT', value: pendenciasTotais }
  ], [totalConcluidos, pendenciasTotais]);

  const COLORS = ['#10B981', '#EF4444'];

  function handleDataPrevistaChange(treinamentoId: string, data: string) {
    setDatasPrevistas(prev => ({
      ...prev,
      [`${selectedAno}_${treinamentoId}`]: data
    }));
  }

  async function handleAddColaborador(e: React.FormEvent) {
    e.preventDefault();
    if (!novoColab.nome || !novoColab.cargo) return alert('Preencha os campos obrigatórios!');
    const { error } = await supabase.from('colaboradores').insert([novoColab]);
    if (!error) {
      setNovoColab({ nome: '', cargo: '', departamento: '', gestor: '' });
      await fetchInitialData();
      alert('Colaborador cadastrado com sucesso!');
    } else alert('Erro ao cadastrar: ' + error.message);
  }

  function startEditingColab(colab: any) {
    setEditingColabId(String(colab.id));
    setEditColabForm({ nome: colab.nome, cargo: colab.cargo, departamento: colab.departamento || '', gestor: colab.gestor || '' });
  }

  async function handleSaveEditColab() {
    if (!editColabForm.nome || !editColabForm.cargo) return alert('Nome e Cargo são obrigatórios!');
    const { error } = await supabase.from('colaboradores').update(editColabForm).eq('id', editingColabId);
    if (!error) {
      setEditingColabId(null);
      await fetchInitialData();
    } else {
      alert('Erro ao atualizar: ' + error.message);
    }
  }

  async function handleDeleteColab(id: string) {
    if (!confirm('Deseja mesmo excluir este colaborador? Todo o histórico de treinamentos dele também será apagado.')) return;
    
    setColaboradores(prev => prev.filter(c => String(c.id) !== String(id)));
    setRegistros(prev => prev.filter(r => String(r.colaborador_id) !== String(id)));
    if (String(selectedColab) === String(id)) setSelectedColab('');

    const { error } = await supabase.from('colaboradores').delete().eq('id', id);
    if (error) {
      alert('Erro ao excluir do banco: ' + error.message);
      await fetchInitialData();
    }
  }

  async function handleAddTreinamento(e: React.FormEvent) {
    e.preventDefault();
    if (!novoTreino.nome_curso) return alert('Informe o nome do treinamento!');
    const { error } = await supabase.from('treinamentos').insert([novoTreino]);
    if (!error) {
      setNovoTreino({ nome_curso: '', carga_horaria: 1, frequencia: 'ANUAL', classificacao: 'Exigência da função', aplicador_padrao: '' });
      await fetchInitialData();
      alert('Treinamento cadastrado com sucesso!');
    } else alert('Erro ao cadastrar: ' + error.message);
  }

  async function handleAddMatriz(e: React.FormEvent) {
    e.preventDefault();
    const cargoFinal = isOutroCargo ? cargoManual.trim() : novaMatriz.cargo.trim();
    if (!cargoFinal || !novaMatriz.treinamento_id) return alert('Selecione ou informe um cargo e escolha o treinamento!');

    const { error } = await supabase.from('matriz_cargo_treinamento').insert([{ cargo: cargoFinal, treinamento_id: novaMatriz.treinamento_id }]);
    if (!error) {
      setNovaMatriz({ cargo: '', treinamento_id: '' });
      setCargoManual('');
      setIsOutroCargo(false);
      await fetchInitialData();
      alert('Vínculo criado na Matriz LNT!');
    } else alert('Erro na Matriz LNT: ' + error.message);
  }

  async function handleDeleteMatrizItem(id: string) {
    if (!confirm('Deseja remover este requisito da Matriz LNT?')) return;
    await supabase.from('matriz_cargo_treinamento').delete().eq('id', id);
    await fetchInitialData();
  }

  function handleToggleStatusPorColaboradorETreinamento(colaboradorId: any, treinamentoId: any) {
    const cId = String(colaboradorId);
    const tId = String(treinamentoId);

    const regExistente = registros.find(r => String(r.colaborador_id) === cId && String(r.treinamento_id) === tId);
    const estaConcluido = !!regExistente;

    const colabObj = colaboradores.find(c => String(c.id) === cId);
    const treinoObj = treinamentos.find(t => String(t.id) === tId);

    if (estaConcluido) {
      setRegistros(prev => prev.filter(r => !(String(r.colaborador_id) === cId && String(r.treinamento_id) === tId)));
      supabase.from('registros').delete().eq('colaborador_id', cId).eq('treinamento_id', tId).then();
    } else {
      const novoRegistro = {
        id: `temp_${Date.now()}`,
        colaborador_id: cId,
        treinamento_id: tId,
        data_realizacao: `${selectedAno}-01-01`,
        instrutor_nome: '',
        aplicador_cargo: '',
        colaboradores: colabObj,
        treinamentos: treinoObj
      };

      setRegistros(prev => [...prev.filter(r => !(String(r.colaborador_id) === cId && String(r.treinamento_id) === tId)), novoRegistro]);
      supabase.from('registros').delete().eq('colaborador_id', cId).eq('treinamento_id', tId).then(() => {
        supabase.from('registros').insert([{
          colaborador_id: cId,
          treinamento_id: tId,
          data_realizacao: novoRegistro.data_realizacao,
          instrutor_nome: '',
          aplicador_cargo: ''
        }]).then();
      });
    }
  }

  function handleGerarCertificado(colaborador: any) {
    setColabCertificado(colaborador);

    const primeiroNome = colaborador.nome.trim().split(' ')[0];
    const cursoNomeSanitizado = currentTreinamento?.nome_curso ? currentTreinamento.nome_curso.replace(/[^a-zA-Z0-9_-]/g, '_') : 'Treinamento';
    const tituloAnterior = document.title;

    document.title = `${cursoNomeSanitizado}_${primeiroNome}`;

    setTimeout(() => {
      window.print();
      setTimeout(() => {
        document.title = tituloAnterior;
      }, 1000);
    }, 300);
  }

  function handleImprimirListaPresenca() {
    setColabCertificado(null);
    const cursoNomeSanitizado = currentTreinamento?.nome_curso ? currentTreinamento.nome_curso.replace(/[^a-zA-Z0-9_-]/g, '_') : 'Treinamento';
    const tituloAnterior = document.title;

    document.title = `Lista_Presenca_${cursoNomeSanitizado}_${selectedAno}`;

    setTimeout(() => {
      window.print();
      setTimeout(() => {
        document.title = tituloAnterior;
      }, 1000);
    }, 200);
  }

  if (!session) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 font-sans p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full border border-slate-200">
          <div className="text-center mb-6">
            <img src="/Logo_Attend_ Ambiental.png" alt="Logo" className="h-16 mx-auto mb-3 object-contain" onError={(e: any) => { e.target.style.display = 'none'; }} />
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">MAQ GESTÃO</h1>
          </div>
          <form onSubmit={handleLogin} className="space-y-4">
            {authError && <div className="bg-red-50 text-red-600 p-3 rounded-lg text-xs font-medium">{authError}</div>}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">E-mail</label>
              <div className="relative">
                <Mail className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm bg-slate-50 outline-none" required />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Senha</label>
              <div className="relative">
                <Lock className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm bg-slate-50 outline-none" required />
              </div>
            </div>
            <button type="submit" disabled={authLoading} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-bold text-sm shadow-md">
              {authLoading ? 'Autenticando...' : 'Entrar no Sistema'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-white">
        <div className="text-center"><div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div><p>Carregando...</p></div>
      </div>
    );
  }

  const filteredColaboradores = colaboradores.filter(c => 
    c.nome.toLowerCase().includes(searchTerm.toLowerCase()) || 
    c.departamento?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.cargo?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const gerirColaboradoresFiltrados = colaboradores.filter(c => 
    c.nome.toLowerCase().includes(searchColabTab.toLowerCase()) || 
    c.departamento?.toLowerCase().includes(searchColabTab.toLowerCase()) ||
    c.cargo?.toLowerCase().includes(searchColabTab.toLowerCase())
  );

  const currentColabData = colaboradores.find(c => String(c.id) === String(selectedColab));
  const colabRegistros = registrosAno.filter(r => String(r.colaborador_id) === String(selectedColab));
  
  const requisitosCargo = currentColabData && currentColabData.cargo ? matrizLnt.filter(m => m.cargo === currentColabData.cargo) : [];
  
  const idsTreinamentosRequeridos = requisitosCargo.map(m => String(m.treinamento_id));
  const treinamentosDoColaborador = treinamentos.filter(t => idsTreinamentosRequeridos.includes(String(t.id)));

  const currentTreinamento = treinamentos.find(t => String(t.id) === String(selectedTreinamentoRelatorio));
  const cargosQueObrigamTreino = currentTreinamento ? matrizLnt.filter(m => String(m.treinamento_id) === String(currentTreinamento.id)).map(m => m.cargo) : [];
  
  const pessoasExigidas = colaboradores.filter(c => cargosQueObrigamTreino.includes(c.cargo));
  const registrosDesseCursoNoAno = registrosAno.filter(r => String(r.treinamento_id) === String(selectedTreinamentoRelatorio));
  const idsColabsConcluidos = registrosDesseCursoNoAno.map(r => String(r.colaborador_id));
  
  const listaRelatorioConcluidos = pessoasExigidas.filter(c => idsColabsConcluidos.includes(String(c.id)));
  const listaRelatorioPendentes = pessoasExigidas.filter(c => !idsColabsConcluidos.includes(String(c.id)));

  return (
    <div className="flex h-screen bg-slate-100 font-sans text-slate-800">
      
      {/* ESTILOS DE IMPRESSÃO */}
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Playfair+Display:ital,wght@0,600;1,400&display=swap');
        
        @media print {
          aside, button, select, header > div:last-child, .no-print {
            display: none !important;
          }
          main {
            padding: 0 !important;
            overflow: visible !important;
            background: white !important;
          }
          .print\\:block {
            display: block !important;
          }
          @page {
            size: ${colabCertificado ? 'A4 landscape' : 'A4 portrait'};
            margin: 6mm;
          }
        }
      `}</style>

      {/* MENU LATERAL COM OPÇÕES DE ANOS EXPANDIDAS E ABA DE CALENDÁRIO */}
      <aside className="w-64 bg-slate-900 text-white p-6 flex flex-col justify-between shadow-xl no-print">
        <div>
          <div className="flex items-center gap-3 mb-6">
            <img src="/Logo_Attend_ Ambiental.png" alt="Logo" className="h-8 w-auto object-contain" onError={(e: any) => { e.target.style.display = 'none'; }} />
            <h1 className="text-xl font-bold tracking-wider">MAQ GESTÃO</h1>
          </div>
          <div className="mb-6 bg-slate-800 p-3 rounded-lg border border-slate-700">
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-1 flex items-center gap-1.5"><CalendarIcon className="w-3.5 h-3.5 text-blue-400" />Ano do Exercício (LNT)</label>
            <select value={selectedAno} onChange={(e) => setSelectedAno(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-600 rounded px-2.5 py-1.5 text-sm font-bold text-white outline-none">
              <option value={2028}>Exercício 2028</option>
              <option value={2027}>Exercício 2027</option>
              <option value={2026}>Exercício 2026</option>
              <option value={2025}>Exercício 2025</option>
              <option value={2024}>Exercício 2024</option>
              <option value={2023}>Exercício 2023</option>
            </select>
          </div>
          <nav className="space-y-2">
            <button onClick={() => { setColabCertificado(null); setActiveTab('relatorio_curso'); }} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'relatorio_curso' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}><Activity className="w-5 h-5" /> Relatório por Curso</button>
            <button onClick={() => { setColabCertificado(null); setActiveTab('dashboard'); }} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}><BarChart className="w-5 h-5" /> Dashboard Executivo</button>
            <button onClick={() => { setColabCertificado(null); setActiveTab('calendario'); }} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'calendario' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}><CalendarIcon className="w-5 h-5" /> Calendário & Agenda</button>
            <button onClick={() => { setColabCertificado(null); setActiveTab('colaborador'); }} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'colaborador' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}><CheckCircle className="w-5 h-5" /> Lançamentos Individuais</button>
            <button onClick={() => { setColabCertificado(null); setActiveTab('matriz_lnt'); }} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'matriz_lnt' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}><Layers className="w-5 h-5" /> Matriz LNT por Cargo</button>
            <button onClick={() => { setColabCertificado(null); setActiveTab('gestao_colabs'); }} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'gestao_colabs' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}><Users className="w-5 h-5" /> Colaboradores</button>
            <button onClick={() => { setColabCertificado(null); setActiveTab('catalogo'); }} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'catalogo' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}><BookOpen className="w-5 h-5" /> Catálogo Treinamentos</button>
            <button onClick={() => { setColabCertificado(null); setActiveTab('gestao_usuarios'); }} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'gestao_usuarios' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}><UserPlus className="w-5 h-5" /> Gestão de Utilizadores</button>
          </nav>
        </div>
        <div className="space-y-3">
          <button onClick={handleImprimirListaPresenca} className="w-full flex items-center gap-2 text-slate-400 hover:text-white text-sm transition"><Printer className="w-4 h-4" /> Imprimir Relatório</button>
          <button onClick={handleLogout} className="w-full flex items-center gap-2 text-red-400 hover:text-red-300 text-sm transition"><LogOut className="w-4 h-4" /> Sair da Conta</button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-8">
        
        {/* CERTIFICADO DE CONCLUSÃO EM A4 PAISAGEM */}
        {colabCertificado && currentTreinamento && (
          <div className="hidden print:flex w-full h-[188mm] p-8 border-[12px] border-slate-900 rounded-3xl bg-white text-center flex-col justify-between relative shadow-2xl box-border">
            <div className="absolute inset-3 border-2 border-amber-500 rounded-2xl pointer-events-none"></div>

            <div className="flex justify-between items-center px-6 pt-2 z-10">
              <img src="/Logo_Attend_ Ambiental.png" alt="Logo" className="h-14 object-contain" onError={(e: any) => { e.target.style.display = 'none'; }} />
              <div className="text-right text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                CERTIFICADO CORPORATIVO DE TREINAMENTO<br />
                CÓDIGO DE VALIDAÇÃO: MAQ-{selectedAno}-{colabCertificado.id}
              </div>
            </div>

            <div className="flex-grow flex flex-col justify-center px-12 z-10 py-6 space-y-4">
              <div>
                <h1 className="text-3xl font-black text-slate-900 tracking-[0.25em] uppercase font-['Cinzel'] border-b-2 border-amber-500 pb-3 inline-block px-12">
                  CERTIFICADO DE CONCLUSÃO
                </h1>
              </div>

              <p className="text-sm text-slate-600 pt-4 leading-relaxed">
                Certificamos para os devidos fins que o(a) colaborador(a)
              </p>

              <h2 className="text-4xl font-extrabold text-slate-900 py-2 font-['Playfair_Display'] italic tracking-wide text-blue-950">
                {colabCertificado.nome}
              </h2>

              <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest pb-4">
                Cargo: <span className="text-slate-800">{colabCertificado.cargo}</span> {colabCertificado.departamento ? `| Setor: ${colabCertificado.departamento}` : ''}
              </p>

              <p className="text-sm text-slate-600">
                Concluiu com aproveitamento o treinamento corporativo de capacitação profissional em:
              </p>

              <div className="bg-slate-50 py-3.5 px-8 rounded-2xl border border-slate-200 max-w-3xl mx-auto my-3 shadow-inner">
                <h3 className="text-2xl font-black text-blue-900 uppercase tracking-wide">
                  {currentTreinamento.nome_curso}
                </h3>
              </div>

              <p className="text-xs text-slate-500 pt-2">
                Carga Horária Total: <strong className="text-slate-800">{currentTreinamento.carga_horaria} Horas</strong> &nbsp;|&nbsp; 
                Classificação: <strong className="text-slate-800">{currentTreinamento.classificacao}</strong> &nbsp;|&nbsp; 
                Exercício: <strong className="text-slate-800">{selectedAno}</strong>
              </p>
            </div>

            <div className="grid grid-cols-2 gap-24 px-16 pb-6 z-10">
              <div className="text-center">
                <div className="border-t-2 border-slate-800 w-64 mx-auto pt-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
                  {colabCertificado.nome}
                  <span className="block text-[10px] font-normal text-slate-500 normal-case mt-0.5">Assinatura do Participante</span>
                </div>
              </div>
              <div className="text-center">
                <div className="border-t-2 border-slate-800 w-64 mx-auto pt-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Instrutor Responsável
                  <span className="block text-[10px] font-normal text-slate-500 normal-case mt-0.5">Assinatura / MTR / Registro</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* RELATÓRIO POR CURSO */}
        {activeTab === 'relatorio_curso' && (
          <div className="space-y-6">
            <header className="flex justify-between items-center border-b pb-4 no-print">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Relatório de Treinamento e Adesão — {selectedAno}</h2>
                <p className="text-slate-500 text-sm">Altere o status, imprima a lista de presença ou emita certificados</p>
              </div>
              <div className="flex items-center gap-3">
                <select 
                  value={selectedTreinamentoRelatorio} 
                  onChange={(e) => setSelectedTreinamentoRelatorio(e.target.value)}
                  className="px-4 py-2 bg-white border border-slate-300 rounded-lg shadow-sm font-semibold text-slate-700 outline-none w-[320px]"
                >
                  <option value="">Selecione o Treinamento...</option>
                  {treinamentos.map(t => <option key={t.id} value={t.id}>{t.nome_curso}</option>)}
                </select>
                <button
                  type="button"
                  onClick={handleImprimirListaPresenca}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 shadow-sm transition"
                >
                  <Printer className="w-4 h-4" /> Lista de Presença (PDF)
                </button>
              </div>
            </header>

            {currentTreinamento ? (
              <div className="space-y-6">
                
                {!colabCertificado && (
                  <div className="hidden print:block mb-6 border-b-2 border-slate-900 pb-4">
                    <div className="flex justify-between items-center mb-4">
                      <div className="flex items-center gap-3">
                        <img src="/Logo_Attend_ Ambiental.png" alt="Logo" className="h-12 w-auto object-contain" onError={(e: any) => { e.target.style.display = 'none'; }} />
                        <h1 className="text-xl font-extrabold text-slate-900 uppercase">LISTA DE PRESENÇA DE TREINAMENTO</h1>
                      </div>
                      <span className="text-sm font-bold text-slate-700">Exercício {selectedAno}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-xs bg-slate-50 p-3 border rounded border-slate-300">
                      <div>
                        <p><strong>Treinamento:</strong> {currentTreinamento.nome_curso}</p>
                        <p className="mt-1"><strong>Carga Horária:</strong> {currentTreinamento.carga_horaria}h | <strong>Classificação:</strong> {currentTreinamento.classificacao}</p>
                      </div>
                      <div>
                        <p><strong>Data de Realização:</strong> ____ / ____ / {selectedAno}</p>
                        <p className="mt-1"><strong>Instrutor:</strong> ___________________________________</p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-6 no-print">
                  <div className="col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h3 className="text-lg font-bold text-slate-900 mb-2">{currentTreinamento.nome_curso}</h3>
                    <p className="text-slate-500 text-sm mb-4">Carga Horária: {currentTreinamento.carga_horaria}h | Classificação: {currentTreinamento.classificacao}</p>
                    
                    <div className="mt-4">
                      <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2">Cargos Exigidos (Matriz LNT):</h4>
                      <div className="flex flex-wrap gap-2">
                        {cargosQueObrigamTreino.length > 0 ? cargosQueObrigamTreino.map(cargo => (
                          <span key={cargo} className="bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-md text-xs font-medium">
                            {cargo}
                          </span>
                        )) : (
                          <span className="text-sm text-slate-400">Nenhum cargo vinculado a este treinamento na Matriz LNT.</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-900 p-6 rounded-xl shadow-sm text-white flex flex-col justify-center items-center text-center">
                    <p className="text-slate-400 text-sm font-medium uppercase mb-2">Adesão do Exercício</p>
                    <div className="flex gap-8">
                      <div>
                        <p className="text-3xl font-extrabold text-emerald-400">{listaRelatorioConcluidos.length}</p>
                        <p className="text-xs text-slate-400 mt-1">Concluídos</p>
                      </div>
                      <div>
                        <p className="text-3xl font-extrabold text-red-400">{listaRelatorioPendentes.length}</p>
                        <p className="text-xs text-slate-400 mt-1">Pendentes</p>
                      </div>
                    </div>
                  </div>
                </div>

                {!colabCertificado && (
                  <div className="hidden print:block">
                    <h3 className="font-bold text-xs uppercase mb-2 text-slate-900">Participantes Convocados</h3>
                    <table className="w-full text-left border-collapse border border-slate-300 text-xs">
                      <thead>
                        <tr className="bg-slate-100 uppercase border-b border-slate-300">
                          <th className="p-2 border-r border-slate-300">Nome do Colaborador</th>
                          <th className="p-2 border-r border-slate-300">Cargo</th>
                          <th className="p-2 border-r border-slate-300">Setor / Área</th>
                          <th className="p-2 w-64">Assinatura do Participante</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-300">
                        {pessoasExigidas.map(c => (
                          <tr key={c.id}>
                            <td className="p-2.5 border-r border-slate-300 font-semibold">{c.nome}</td>
                            <td className="p-2.5 border-r border-slate-300">{c.cargo}</td>
                            <td className="p-2.5 border-r border-slate-300">{c.departamento || '-'}</td>
                            <td className="p-2.5"></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    
                    <div className="mt-16 flex justify-center text-xs text-slate-700">
                      <div className="text-center w-72 border-t border-slate-600 pt-1">
                        <strong>Assinatura do Instrutor Responsável</strong>
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-6 no-print">
                  <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="bg-emerald-50 border-b border-emerald-100 p-4">
                      <h3 className="font-bold text-emerald-800 flex items-center gap-2"><CheckCircle className="w-5 h-5"/> Pessoal com Treinamento Concluído ({listaRelatorioConcluidos.length})</h3>
                    </div>
                    <ul className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                      {listaRelatorioConcluidos.map(c => (
                        <li key={c.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition">
                          <div>
                            <p className="font-semibold text-slate-800 text-sm">{c.nome}</p>
                            <p className="text-xs text-slate-500 mt-0.5">{c.cargo} • {c.departamento}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => handleGerarCertificado(c)}
                              className="cursor-pointer px-2.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs flex items-center gap-1 shadow-sm transition"
                              title="Gerar Certificado Individual em PDF"
                            >
                              <Award className="w-3.5 h-3.5" />
                              <span>🎓 Diploma</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleToggleStatusPorColaboradorETreinamento(c.id, selectedTreinamentoRelatorio)}
                              className="cursor-pointer px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-rose-600 text-white font-bold text-xs flex items-center gap-1 shadow-sm transition active:scale-95"
                            >
                              <CheckCircle className="w-3.5 h-3.5" />
                              <span>🟢 Concluído</span>
                            </button>
                          </div>
                        </li>
                      ))}
                      {listaRelatorioConcluidos.length === 0 && <li className="p-6 text-center text-slate-400 text-sm">Ninguém concluiu este treinamento.</li>}
                    </ul>
                  </div>

                  <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="bg-red-50 border-b border-red-100 p-4">
                      <h3 className="font-bold text-red-800 flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Pessoal Pendente na LNT ({listaRelatorioPendentes.length})</h3>
                    </div>
                    <ul className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                      {listaRelatorioPendentes.map(c => (
                        <li key={c.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition">
                          <div>
                            <p className="font-semibold text-slate-800 text-sm">{c.nome}</p>
                            <p className="text-xs text-slate-500 mt-0.5">{c.cargo} • {c.departamento}</p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleToggleStatusPorColaboradorETreinamento(c.id, selectedTreinamentoRelatorio)}
                            className="cursor-pointer px-3 py-1.5 rounded-lg bg-rose-500 hover:bg-emerald-600 text-white font-bold text-xs flex items-center gap-1 shadow-sm transition active:scale-95"
                          >
                            <X className="w-3.5 h-3.5" />
                            <span>🔴 Marcar Concluído</span>
                          </button>
                        </li>
                      ))}
                      {listaRelatorioPendentes.length === 0 && cargosQueObrigamTreino.length > 0 && <li className="p-6 text-center text-slate-400 text-sm">Nenhuma pendência. Todos concluíram!</li>}
                      {cargosQueObrigamTreino.length === 0 && <li className="p-6 text-center text-slate-400 text-sm">Este treinamento não possui requisitos na LNT.</li>}
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center p-8 bg-white rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 font-medium">Selecione um treinamento no menu acima.</p>
              </div>
            )}
          </div>
        )}

        {/* DASHBOARD EXECUTIVO */}
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            <header className="flex justify-between items-center border-b pb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Dashboard Executivo — Exercício {selectedAno}</h2>
                <p className="text-slate-500 text-sm">Visão geral do cumprimento de compliance e carga horária por treinamento</p>
              </div>
            </header>

            <div className="grid grid-cols-6 gap-4">
              <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                  <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Total Quadro</p>
                  <h3 className="text-2xl font-extrabold text-slate-900 mt-1">{colaboradores.length}</h3>
                  <span className="text-[10px] text-slate-400 font-medium mt-0.5 block">Colaboradores</span>
                </div>
                <div className="bg-slate-100 p-2.5 rounded-xl text-slate-600"><Users className="w-5 h-5" /></div>
              </div>

              <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                  <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Pessoas Mapeadas</p>
                  <h3 className="text-2xl font-extrabold text-blue-600 mt-1">{pessoasMapeadas.length}</h3>
                  <span className="text-[10px] text-blue-600 font-medium mt-0.5 block">{colaboradores.length ? Math.round((pessoasMapeadas.length / colaboradores.length) * 100) : 0}% da Equipa</span>
                </div>
                <div className="bg-blue-50 p-2.5 rounded-xl text-blue-600"><UserCheck className="w-5 h-5" /></div>
              </div>

              <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                  <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Treinamentos</p>
                  <h3 className="text-2xl font-extrabold text-purple-600 mt-1">{treinamentos.length}</h3>
                  <span className="text-[10px] text-purple-600 font-medium mt-0.5 block">No Catálogo</span>
                </div>
                <div className="bg-purple-50 p-2.5 rounded-xl text-purple-600"><BookOpen className="w-5 h-5" /></div>
              </div>

              <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                  <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Compliance LNT</p>
                  <h3 className="text-2xl font-extrabold text-emerald-600 mt-1">{complianceTaxa}%</h3>
                  <span className="text-[10px] text-emerald-600 font-medium mt-0.5 block">{totalConcluidos} Concluídos</span>
                </div>
                <div className="bg-emerald-50 p-2.5 rounded-xl text-emerald-600"><TrendingUp className="w-5 h-5" /></div>
              </div>

              <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                  <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Horas de Treino</p>
                  <h3 className="text-2xl font-extrabold text-amber-600 mt-1">{totalHoras}h</h3>
                  <span className="text-[10px] text-slate-400 font-medium mt-0.5 block">Acumulado ({selectedAno})</span>
                </div>
                <div className="bg-amber-50 p-2.5 rounded-xl text-amber-600"><Award className="w-5 h-5" /></div>
              </div>

              <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
                <div>
                  <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Média de Horas</p>
                  <h3 className="text-2xl font-extrabold text-indigo-600 mt-1">{mediaHorasPorPessoa}h</h3>
                  <span className="text-[10px] text-indigo-600 font-medium mt-0.5 block">Por Pessoa Mapeada</span>
                </div>
                <div className="bg-indigo-50 p-2.5 rounded-xl text-indigo-600"><Clock className="w-5 h-5" /></div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-8">
              
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="text-lg font-bold text-slate-800">Compliance Matriz LNT</h4>
                  <span className="text-xs font-bold text-slate-400 uppercase">Exercício {selectedAno}</span>
                </div>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={statusData} cx="50%" cy="50%" innerRadius={70} outerRadius={95} dataKey="value">
                        {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip formatter={(val) => [`${val} Colaboradores`, 'Quantidade']} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-2 text-xs font-semibold">
                  <span className="flex items-center gap-1.5 text-emerald-600"><span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span> Concluídos ({totalConcluidos})</span>
                  <span className="flex items-center gap-1.5 text-red-500"><span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span> Pendentes ({pendenciasTotais})</span>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="text-lg font-bold text-slate-800">Conclusões por Setor</h4>
                  <span className="text-xs font-bold text-slate-400 uppercase">Adesão por Área</span>
                </div>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dadosPorDepartamento} layout="vertical" margin={{ top: 10, right: 20, left: 40, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                      <XAxis type="number" />
                      <YAxis dataKey="setor" type="category" tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(val) => [`${val} Treinamentos Concluídos`, 'Total']} />
                      <Bar dataKey="concluidos" fill="#10B981" radius={[0, 4, 4, 0]} barSize={20} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h4 className="text-lg font-bold text-slate-800">Carga Horária por Treinamento (Horas)</h4>
                  <p className="text-slate-400 text-xs">Passe o mouse sobre as barras para ver a norma e a carga horária detalhada</p>
                </div>
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dadosGraficoTreinamentos} margin={{ top: 20, right: 30, left: 20, bottom: 85 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis 
                      dataKey="nomeAbreviado" 
                      interval={0} 
                      angle={-35} 
                      textAnchor="end" 
                      height={80} 
                      tick={{ fontSize: 11, fill: '#475569' }} 
                    />
                    <YAxis label={{ value: 'Horas', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#64748B' } }} />
                    <Tooltip 
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl text-xs space-y-1">
                              <p className="font-bold text-blue-400">{data.nomeCompleto}</p>
                              <p>Carga Horária: <strong className="text-emerald-400">{data.carga_horaria} horas</strong></p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar dataKey="carga_horaria" fill="#3B82F6" radius={[6, 6, 0, 0]} barSize={35} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        )}

        {/* NOVA ABA: CALENDÁRIO & CRONOGRAMA DE APLICAÇÃO PREVISTA */}
        {activeTab === 'calendario' && (
          <div className="space-y-6">
            <header className="flex justify-between items-center border-b pb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Calendário de Treinamentos — Exercício {selectedAno}</h2>
                <p className="text-slate-500 text-sm">Defina as datas previstas de aplicação de cada treinamento para o ano selecionado</p>
              </div>
            </header>

            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
                <h3 className="font-semibold text-slate-700 flex items-center gap-2">
                  <CalendarIcon className="w-4 h-4 text-blue-600" />
                  Planejamento Anual de Aplicação ({treinamentos.length} Treinamentos)
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-white border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
                    <tr>
                      <th className="p-4">Treinamento / Norma</th>
                      <th className="p-4">Carga Horária</th>
                      <th className="p-4">Classificação</th>
                      <th className="p-4">Data Prevista de Aplicação</th>
                      <th className="p-4 text-center">Status no Exercício</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {treinamentos.map(t => {
                      const keyPrevista = `${selectedAno}_${t.id}`;
                      const dataAtual = datasPrevistas[keyPrevista] || '';
                      
                      const concluidosCount = registrosAno.filter(r => String(r.treinamento_id) === String(t.id)).length;
                      const cargosExigidos = matrizLnt.filter(m => String(m.treinamento_id) === String(t.id)).map(m => m.cargo);
                      const totalPessoasExigidas = colaboradores.filter(c => cargosExigidos.includes(c.cargo)).length;

                      const isConcluidoTotal = totalPessoasExigidas > 0 && concluidosCount >= totalPessoasExigidas;

                      return (
                        <tr key={t.id} className="hover:bg-slate-50 transition">
                          <td className="p-4 font-bold text-slate-900">{t.nome_curso}</td>
                          <td className="p-4 text-slate-600">{t.carga_horaria}h</td>
                          <td className="p-4 text-slate-600">{t.classificacao}</td>
                          <td className="p-4">
                            <input 
                              type="date" 
                              value={dataAtual}
                              onChange={(e) => handleDataPrevistaChange(String(t.id), e.target.value)}
                              className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </td>
                          <td className="p-4 text-center">
                            {isConcluidoTotal ? (
                              <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-bold inline-flex items-center gap-1">
                                <CheckCircle className="w-3.5 h-3.5" /> Concluído
                              </span>
                            ) : concluidosCount > 0 ? (
                              <span className="bg-blue-100 text-blue-800 text-xs px-2.5 py-1 rounded-full font-bold">
                                em Andamento ({concluidosCount}/{totalPessoasExigidas})
                              </span>
                            ) : (
                              <span className="bg-amber-100 text-amber-800 text-xs px-2.5 py-1 rounded-full font-bold">
                                Previsto ({totalPessoasExigidas} Pessoas)
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* LANÇAMENTOS INDIVIDUAIS */}
        {activeTab === 'colaborador' && (
          <div className="space-y-6">
            <header className="flex justify-between items-center border-b pb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Lançamentos Individuais</h2>
                <p className="text-slate-500 text-sm">Controle as LNTs do funcionário selecionado</p>
              </div>
              <div className="flex gap-4">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                  <input type="text" placeholder="Filtrar colaborador..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-9 pr-4 py-2 border rounded-lg text-sm" />
                </div>
                <select value={selectedColab} onChange={(e) => setSelectedColab(e.target.value)} className="px-4 py-2 border border-slate-300 rounded-lg shadow-sm font-semibold text-slate-700 outline-none w-80">
                  <option value="">Selecione um colaborador...</option>
                  {filteredColaboradores.map(c => <option key={c.id} value={c.id}>{c.nome} ({c.cargo})</option>)}
                </select>
              </div>
            </header>

            {currentColabData ? (
              <>
                <div className="bg-slate-900 text-white p-6 rounded-xl shadow-lg flex justify-between items-center">
                  <div>
                    <h3 className="text-2xl font-bold">{currentColabData.nome}</h3>
                    <p className="text-slate-300 text-sm mt-1">Cargo: <span className="font-semibold text-blue-400">{currentColabData.cargo}</span> | Setor: {currentColabData.departamento}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-400">GESTOR DIRETO</p>
                    <p className="font-semibold">{currentColabData.gestor || 'Não informado'}</p>
                  </div>
                </div>

                {requisitosCargo.length > 0 ? (
                  <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl text-blue-800 text-sm flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
                    <div>
                      <strong>Requisitos exigidos para ({currentColabData.cargo}):</strong>
                      <span className="ml-2">{requisitosCargo.map(r => r.treinamentos?.nome_curso).join(', ')}</span>
                    </div>
                  </div>
                ) : (
                  <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl text-amber-800 text-sm flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                    <div>
                      <strong>Nenhum curso exigido na Matriz LNT:</strong> O cargo <span className="font-semibold">{currentColabData.cargo}</span> ainda não possui vinculação na aba Matriz LNT.
                    </div>
                  </div>
                )}

                <div className="space-y-4 mt-6">
                  {treinamentosDoColaborador.map(treino => {
                    const reg = colabRegistros.find(r => String(r.treinamento_id) === String(treino.id));
                    const isConcluidoBD = !!reg;

                    return (
                      <div key={`${selectedColab}_${treino.id}_${selectedAno}`} className="bg-white p-6 rounded-xl border border-l-4 border-l-blue-500 border-slate-200 shadow-sm flex items-center justify-between gap-6">
                        <div className="w-1/3">
                          <div className="flex items-center gap-2">
                            <h4 className="font-bold text-slate-900 text-lg">{treino.nome_curso}</h4>
                            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded font-semibold">Exigido</span>
                          </div>
                          <p className="text-slate-500 text-sm">{treino.carga_horaria}h — {treino.classificacao}</p>
                          {reg?.url_forms && <a href={reg.url_forms} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-2"><ExternalLink className="w-3 h-3" /> Ver Evidência Anexada</a>}
                        </div>
                        
                        <div className="flex-1 flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => handleToggleStatusPorColaboradorETreinamento(selectedColab, treino.id)}
                            className={`cursor-pointer px-4 py-2.5 rounded-xl font-extrabold text-sm flex items-center gap-2 shadow-sm transition-all duration-150 transform active:scale-95 border ${
                              isConcluidoBD 
                                ? 'bg-emerald-500 hover:bg-emerald-600 text-white border-emerald-600' 
                                : 'bg-rose-500 hover:bg-rose-600 text-white border-rose-600'
                            }`}
                          >
                            {isConcluidoBD ? <CheckCircle className="w-4 h-4" /> : <X className="w-4 h-4" />}
                            {isConcluidoBD ? '🟢 Concluído' : '🔴 Pendente'}
                          </button>
                        </div>
                      </div>
                    );
                  })}

                  {treinamentosDoColaborador.length === 0 && (
                    <div className="text-center p-12 bg-white rounded-xl shadow-sm border border-slate-200">
                      <p className="text-slate-600 font-semibold text-base">Nenhum treinamento vinculado ao cargo "{currentColabData.cargo}".</p>
                      <p className="text-slate-400 text-sm mt-1">Para associar requisitos a esta função, acesse a aba <strong className="text-blue-600">Matriz LNT por Cargo</strong>.</p>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center p-8 bg-white rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 font-medium">Aguarde ou Selecione um colaborador válido no menu acima.</p>
              </div>
            )}
          </div>
        )}

        {/* MATRIZ LNT */}
        {activeTab === 'matriz_lnt' && (
          <div className="space-y-6">
            <header className="border-b pb-4"><h2 className="text-2xl font-bold text-slate-900">Matriz LNT</h2></header>
            <form onSubmit={handleAddMatriz} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex gap-4 items-end max-w-3xl">
              <div className="flex-1">
                <div className="flex justify-between items-center mb-1">
                  <label className="block text-xs font-medium text-slate-700">Cargo</label>
                  <button type="button" onClick={() => setIsOutroCargo(!isOutroCargo)} className="text-xs text-blue-600 flex items-center gap-1"><Edit3 className="w-3 h-3" />{isOutroCargo ? 'Selecionar da Lista' : '+ Novo Cargo'}</button>
                </div>
                {isOutroCargo ? (
                  <input type="text" value={cargoManual} onChange={e => setCargoManual(e.target.value)} className="w-full p-2 border rounded-lg text-sm" required />
                ) : (
                  <select value={novaMatriz.cargo} onChange={e => { if (e.target.value === '__OUTRO__') setIsOutroCargo(true); else setNovaMatriz({...novaMatriz, cargo: e.target.value}); }} className="w-full p-2 border rounded-lg text-sm" required>
                    <option value="">Selecione o cargo...</option>
                    {cargosUnicos.map(cargo => <option key={cargo} value={cargo}>{cargo}</option>)}
                    <option value="__OUTRO__">+ Novo Cargo...</option>
                  </select>
                )}
              </div>
              <div className="flex-1">
                <label className="block text-xs font-medium text-slate-700 mb-1">Treinamento</label>
                <select value={novaMatriz.treinamento_id} onChange={e => setNovaMatriz({...novaMatriz, treinamento_id: e.target.value})} className="w-full p-2 border rounded-lg text-sm" required>
                  <option value="">Selecione...</option>
                  {treinamentos.map(t => <option key={t.id} value={t.id}>{t.nome_curso}</option>)}
                </select>
              </div>
              <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold text-sm flex items-center gap-2"><Plus className="w-4 h-4" /> Vincular</button>
            </form>
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold"><tr><th className="p-4">Cargo</th><th className="p-4">Treinamento</th><th className="p-4 text-right">Ação</th></tr></thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {matrizLnt.map(m => (
                    <tr key={m.id} className="hover:bg-slate-50"><td className="p-4 font-bold">{m.cargo}</td><td className="p-4 text-blue-600">{m.treinamentos?.nome_curso}</td><td className="p-4 text-right"><button onClick={() => handleDeleteMatrizItem(m.id)} className="text-red-500 hover:text-red-700"><Trash2 className="w-4 h-4" /></button></td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* GESTÃO DE COLABORADORES */}
        {activeTab === 'gestao_colabs' && (
          <div className="space-y-6">
            <header className="border-b pb-4 flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Gestão de Colaboradores</h2>
                <p className="text-slate-500 text-sm">Adicione, edite ou exclua funcionários da base corporativa</p>
              </div>
            </header>

            <form onSubmit={handleAddColaborador} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-end gap-4">
              <div className="flex-1">
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Nome Completo</label>
                <input type="text" value={novoColab.nome} onChange={e => setNovoColab({...novoColab, nome: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" required placeholder="Ex: João Silva" />
              </div>
              <div className="flex-1">
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Cargo</label>
                <input type="text" value={novoColab.cargo} onChange={e => setNovoColab({...novoColab, cargo: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" required placeholder="Ex: Operador" />
              </div>
              <div className="flex-1">
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Setor</label>
                <input type="text" value={novoColab.departamento} onChange={e => setNovoColab({...novoColab, departamento: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" placeholder="Ex: Produção" />
              </div>
              <div className="flex-1">
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Gestor Direto</label>
                <input type="text" value={novoColab.gestor} onChange={e => setNovoColab({...novoColab, gestor: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" placeholder="Ex: Maria Costa" />
              </div>
              <button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded-lg font-semibold text-sm flex items-center gap-2">
                <Plus className="w-4 h-4" /> Adicionar
              </button>
            </form>

            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
                <h3 className="font-semibold text-slate-700">Equipa Cadastrada ({colaboradores.length})</h3>
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                  <input type="text" placeholder="Procurar pessoa..." value={searchColabTab} onChange={(e) => setSearchColabTab(e.target.value)} className="pl-9 pr-4 py-1.5 border rounded-lg text-sm w-64 outline-none" />
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[800px]">
                  <thead className="bg-white border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
                    <tr>
                      <th className="p-4">Nome do Colaborador</th>
                      <th className="p-4">Cargo</th>
                      <th className="p-4">Setor</th>
                      <th className="p-4">Gestor Direto</th>
                      <th className="p-4 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {gerirColaboradoresFiltrados.map(c => (
                      <tr key={c.id} className="hover:bg-slate-50 transition">
                        {editingColabId === String(c.id) ? (
                          <>
                            <td className="p-3"><input type="text" value={editColabForm.nome} onChange={e => setEditColabForm({...editColabForm, nome: e.target.value})} className="w-full p-1.5 border rounded text-sm outline-none ring-2 ring-blue-200" /></td>
                            <td className="p-3"><input type="text" value={editColabForm.cargo} onChange={e => setEditColabForm({...editColabForm, cargo: e.target.value})} className="w-full p-1.5 border rounded text-sm outline-none ring-2 ring-blue-200" /></td>
                            <td className="p-3"><input type="text" value={editColabForm.departamento} onChange={e => setEditColabForm({...editColabForm, departamento: e.target.value})} className="w-full p-1.5 border rounded text-sm outline-none" /></td>
                            <td className="p-3"><input type="text" value={editColabForm.gestor} onChange={e => setEditColabForm({...editColabForm, gestor: e.target.value})} className="w-full p-1.5 border rounded text-sm outline-none" /></td>
                            <td className="p-3 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <button onClick={handleSaveEditColab} className="text-emerald-600 hover:text-emerald-800 font-semibold px-2 py-1 bg-emerald-50 rounded">Salvar</button>
                                <button onClick={() => setEditingColabId(null)} className="text-slate-500 hover:text-slate-700 px-2 py-1"><X className="w-4 h-4" /></button>
                              </div>
                            </td>
                          </>
                        ) : (
                          <>
                            <td className="p-4 font-semibold text-slate-900">{c.nome}</td>
                            <td className="p-4 text-slate-600">{c.cargo}</td>
                            <td className="p-4 text-slate-600">{c.departamento || '-'}</td>
                            <td className="p-4 text-slate-600">{c.gestor || '-'}</td>
                            <td className="p-4 text-right">
                              <button onClick={() => startEditingColab(c)} className="text-blue-500 hover:text-blue-700 p-1.5 rounded transition">
                                <Edit3 className="w-4 h-4" />
                              </button>
                              <button onClick={() => handleDeleteColab(c.id)} className="text-red-500 hover:text-red-700 p-1.5 rounded transition ml-2">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                    {gerirColaboradoresFiltrados.length === 0 && (
                      <tr>
                        <td colSpan={5} className="p-8 text-center text-slate-500">Nenhum colaborador encontrado com esta busca.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* CATÁLOGO */}
        {activeTab === 'catalogo' && (
          <div className="space-y-6">
            <header className="border-b pb-4"><h2 className="text-2xl font-bold text-slate-900">Catálogo de Treinamentos</h2></header>
            <form onSubmit={handleAddTreinamento} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm grid grid-cols-5 gap-4 items-end">
              <div><label className="block text-xs font-medium mb-1">Nome</label><input type="text" value={novoTreino.nome_curso} onChange={e => setNovoTreino({...novoTreino, nome_curso: e.target.value})} className="w-full p-2 border rounded-lg text-sm" required /></div>
              <div><label className="block text-xs font-medium mb-1">Carga Horária</label><input type="number" step="0.5" value={novoTreino.carga_horaria} onChange={e => setNovoTreino({...novoTreino, carga_horaria: parseFloat(e.target.value)})} className="w-full p-2 border rounded-lg text-sm" /></div>
              <div><label className="block text-xs font-medium mb-1">Frequência</label><input type="text" value={novoTreino.frequencia} onChange={e => setNovoTreino({...novoTreino, frequencia: e.target.value})} className="w-full p-2 border rounded-lg text-sm" /></div>
              <div><label className="block text-xs font-medium mb-1">Classificação</label><input type="text" value={novoTreino.classificacao} onChange={e => setNovoTreino({...novoTreino, classificacao: e.target.value})} className="w-full p-2 border rounded-lg text-sm" /></div>
              <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold text-sm flex justify-center gap-2"><Plus className="w-4 h-4" /> Criar</button>
            </form>
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold"><tr><th className="p-4">Norma</th><th className="p-4">Horas</th><th className="p-4">Frequência</th><th className="p-4">Classificação</th></tr></thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {treinamentos.map(t => <tr key={t.id} className="hover:bg-slate-50"><td className="p-4 font-bold text-slate-900">{t.nome_curso}</td><td className="p-4">{t.carga_horaria}h</td><td className="p-4">{t.frequencia}</td><td className="p-4">{t.classificacao}</td></tr>)}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* GESTÃO DE UTILIZADORES */}
        {activeTab === 'gestao_usuarios' && (
          <div className="space-y-6">
            <header className="border-b pb-4"><h2 className="text-2xl font-bold text-slate-900">Acessos</h2></header>
            <form onSubmit={handleCreateUser} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm max-w-md space-y-4">
              {userSuccess && <div className="bg-emerald-50 text-emerald-700 p-3 rounded-lg text-xs font-semibold">{userSuccess}</div>}
              <div><label className="block text-xs font-semibold mb-1">E-mail</label><input type="email" value={novoUsuario.email} onChange={e => setNovoUsuario({...novoUsuario, email: e.target.value})} className="w-full p-2 border rounded-lg text-sm" required /></div>
              <div><label className="block text-xs font-semibold mb-1">Senha</label><input type="password" value={novoUsuario.password} onChange={e => setNovoUsuario({...novoUsuario, password: e.target.value})} className="w-full p-2 border rounded-lg text-sm" required /></div>
              <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold text-sm flex justify-center gap-2"><UserPlus className="w-4 h-4" /> Criar Acesso</button>
            </form>
          </div>
        )}

      </main>
    </div>
  );
}