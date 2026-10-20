'use client';

import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { 
  Users, Award, BookOpen, CheckCircle, AlertTriangle, FileText, Upload, Save, Plus, Search, Printer, Layers, ExternalLink, Trash2, LogOut, Lock, Mail, UserPlus, Shield, Calendar
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

  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedAno, setSelectedAno] = useState<number>(new Date().getFullYear());
  const [colaboradores, setColaboradores] = useState<any[]>([]);
  const [treinamentos, setTreinamentos] = useState<any[]>([]);
  const [registros, setRegistros] = useState<any[]>([]);
  const [matrizLnt, setMatrizLnt] = useState<any[]>([]);
  const [selectedColab, setSelectedColab] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Formulários de cadastro
  const [novoColab, setNovoColab] = useState({ nome: '', cargo: '', departamento: '', gestor: '' });
  const [novoTreino, setNovoTreino] = useState({ nome_curso: '', carga_horaria: 1, frequencia: 'ANUAL', classificacao: 'Exigência da função', aplicador_padrao: '' });
  const [novaMatriz, setNovaMatriz] = useState({ cargo: '', treinamento_id: '' });
  
  // Formulário de gestão de utilizadores
  const [novoUsuario, setNovoUsuario] = useState({ email: '', password: '' });
  const [userSuccess, setUserSuccess] = useState('');

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

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      setAuthError('Falha na autenticação: ' + error.message);
    }
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

    const { data, error } = await supabase.auth.signUp({
      email: novoUsuario.email,
      password: novoUsuario.password,
    });

    if (error) {
      alert('Erro ao criar utilizador: ' + error.message);
    } else {
      setUserSuccess(`Utilizador ${novoUsuario.email} criado com sucesso!`);
      setNovoUsuario({ email: '', password: '' });
    }
  }

  async function fetchInitialData() {
    setLoading(true);
    const { data: colabs } = await supabase.from('colaboradores').select('*').order('nome');
    const { data: treinos } = await supabase.from('treinamentos').select('*').order('nome_curso');
    const { data: regs } = await supabase.from('registros').select('*, colaboradores(nome, departamento, cargo), treinamentos(nome_curso, carga_horaria, classificacao)');
    const { data: matriz } = await supabase.from('matriz_cargo_treinamento').select('*, treinamentos(nome_curso, carga_horaria)');

    if (colabs) setColaboradores(colabs);
    if (treinos) setTreinamentos(treinos);
    if (regs) setRegistros(regs);
    if (matriz) setMatrizLnt(matriz);
    if (colabs && colabs.length > 0 && !selectedColab) setSelectedColab(colabs[0].id);
    setLoading(false);
  }

  // Filtragem de Registros pelo Ano Selecionado
  const registrosAno = registros.filter(r => {
    if (!r.data_realizacao) return true;
    const ano = new Date(r.data_realizacao).getFullYear();
    return ano === selectedAno;
  });

  // Métricas do Dashboard Reativas ao Ano Selecionado
  const totalHoras = registrosAno.reduce((acc, r) => {
    const horas = Number(r.treinamentos?.carga_horaria) || 0;
    return acc + horas;
  }, 0);

  const totalConcluidos = registrosAno.length;
  
  const statusData = [
    { name: '🟢 Concluídos', value: totalConcluidos },
    { name: '🔴 Pendentes LNT', value: Math.max(0, matrizLnt.length - totalConcluidos) }
  ];
  const COLORS = ['#10B981', '#EF4444'];

  async function handleAddColaborador(e: React.FormEvent) {
    e.preventDefault();
    if (!novoColab.nome || !novoColab.cargo) return alert('Preencha os campos obrigatórios!');
    const { error } = await supabase.from('colaboradores').insert([novoColab]);
    if (!error) {
      setNovoColab({ nome: '', cargo: '', departamento: '', gestor: '' });
      fetchInitialData();
      alert('Colaborador cadastrado com sucesso!');
    } else {
      alert('Erro ao cadastrar: ' + error.message);
    }
  }

  async function handleAddTreinamento(e: React.FormEvent) {
    e.preventDefault();
    if (!novoTreino.nome_curso) return alert('Informe o nome do treinamento!');
    const { error } = await supabase.from('treinamentos').insert([novoTreino]);
    if (!error) {
      setNovoTreino({ nome_curso: '', carga_horaria: 1, frequencia: 'ANUAL', classificacao: 'Exigência da função', aplicador_padrao: '' });
      fetchInitialData();
      alert('Treinamento cadastrado com sucesso!');
    } else {
      alert('Erro ao cadastrar: ' + error.message);
    }
  }

  async function handleAddMatriz(e: React.FormEvent) {
    e.preventDefault();
    if (!novaMatriz.cargo || !novaMatriz.treinamento_id) return alert('Selecione o cargo e o treinamento!');
    const { error } = await supabase.from('matriz_cargo_treinamento').insert([novaMatriz]);
    if (!error) {
      setNovaMatriz({ cargo: '', treinamento_id: '' });
      fetchInitialData();
      alert('Vínculo criado na Matriz LNT!');
    } else {
      alert('Erro na Matriz LNT: ' + error.message);
    }
  }

  async function handleDeleteMatrizItem(id: string) {
    if (!confirm('Deseja remover este requisito da Matriz LNT?')) return;
    await supabase.from('matriz_cargo_treinamento').delete().eq('id', id);
    fetchInitialData();
  }

  async function handleSalvarRegistroDirect(
    treinamentoId: string, 
    novoStatus: string, 
    dataAplicacao: string, 
    aplicador: string, 
    cargoAplicador: string, 
    arquivoFile: File | null
  ) {
    let urlForms = '';

    if (arquivoFile) {
      const fileName = `evidencia_${selectedColab}_${treinamentoId}_${Date.now()}.pdf`;
      const { data, error } = await supabase.storage.from('evidencias').upload(fileName, arquivoFile);
      if (!error && data) {
        urlForms = supabase.storage.from('evidencias').getPublicUrl(data.path).data.publicUrl;
      }
    }

    const querConcluir = novoStatus.includes('Concluid') || novoStatus.includes('Concluíd');

    if (querConcluir) {
      const treinoObj = treinamentos.find(t => t.id === treinamentoId);
      const colabObj = colaboradores.find(c => c.id === selectedColab);

      const payload: any = {
        colaborador_id: selectedColab,
        treinamento_id: treinamentoId,
        data_realizacao: dataAplicacao || `${selectedAno}-01-01`,
        instrutor_nome: aplicador || '',
        aplicador_cargo: cargoAplicador || ''
      };
      if (urlForms) payload.url_forms = urlForms;

      const { error: delError } = await supabase
        .from('registros')
        .delete()
        .eq('colaborador_id', selectedColab)
        .eq('treinamento_id', treinamentoId);

      if (delError) {
        console.error('Erro ao deletar prévio:', delError.message);
      }

      const { data: insertedData, error: insError } = await supabase
        .from('registros')
        .insert([payload])
        .select('*, colaboradores(nome, departamento, cargo), treinamentos(nome_curso, carga_horaria, classificacao)');

      if (insError) {
        alert('Erro ao salvar registro no banco Supabase: ' + insError.message);
      } else {
        alert('Treinamento registrado como CONCLUÍDO!');
        const itemInserido = (insertedData && insertedData[0]) ? insertedData[0] : {
          ...payload,
          id: `local_${Date.now()}`,
          colaboradores: colabObj,
          treinamentos: treinoObj
        };

        setRegistros(prev => [
          ...prev.filter(r => !(r.colaborador_id === selectedColab && r.treinamento_id === treinamentoId)),
          itemInserido
        ]);
      }
    } else {
      const { error: delError } = await supabase
        .from('registros')
        .delete()
        .eq('colaborador_id', selectedColab)
        .eq('treinamento_id', treinamentoId);

      if (delError) {
        alert('Erro ao remover registro do banco Supabase: ' + delError.message);
      } else {
        alert('Treinamento alterado para PENDENTE!');
        setRegistros(prev => prev.filter(r => !(r.colaborador_id === selectedColab && r.treinamento_id === treinamentoId)));
      }
    }
  }

  // TELA DE LOGIN
  if (!session) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 font-sans p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full border border-slate-200">
          <div className="text-center mb-6">
            <img 
              src="/Logo_Attend_ Ambiental.png" 
              alt="Logo Attend Ambiental" 
              className="h-16 mx-auto mb-3 object-contain"
              onError={(e: any) => { e.target.style.display = 'none'; }}
            />
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">MAQ GESTÃO</h1>
            <p className="text-slate-500 text-sm mt-1">Acesso ao Sistema de Treinamentos</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {authError && (
              <div className="bg-red-50 text-red-600 p-3 rounded-lg text-xs font-medium border border-red-200">
                {authError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">E-mail Corporativo</label>
              <div className="relative">
                <Mail className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
                <input 
                  type="email" 
                  value={email} 
                  onChange={e => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm bg-slate-50 outline-none focus:ring-2 focus:ring-blue-500"
                  required 
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Senha de Acesso</label>
              <div className="relative">
                <Lock className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
                <input 
                  type="password" 
                  value={password} 
                  onChange={e => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm bg-slate-50 outline-none focus:ring-2 focus:ring-blue-500"
                  required 
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={authLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-bold text-sm shadow-md transition duration-150 flex items-center justify-center gap-2"
            >
              {authLoading ? 'Autenticando...' : 'Entrar no Sistema'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-white font-sans">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg font-medium">Carregando MAQ Gestão de Treinamentos...</p>
        </div>
      </div>
    );
  }

  const filteredColaboradores = colaboradores.filter(c => 
    c.nome.toLowerCase().includes(searchTerm.toLowerCase()) || 
    c.departamento?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.cargo?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const currentColabData = colaboradores.find(c => c.id === selectedColab);
  const colabRegistros = registrosAno.filter(r => r.colaborador_id === selectedColab);
  const requisitosCargo = matrizLnt.filter(m => m.cargo === currentColabData?.cargo);
  const cargosExistentes = Array.from(new Set(colaboradores.map(c => c.cargo).filter(Boolean)));

  return (
    <div className="flex h-screen bg-slate-100 font-sans text-slate-800">
      {/* Menu Lateral */}
      <aside className="w-64 bg-slate-900 text-white p-6 flex flex-col justify-between shadow-xl">
        <div>
          <div className="flex items-center gap-3 mb-6">
            <img 
              src="/Logo_Attend_ Ambiental.png" 
              alt="Logo" 
              className="h-8 w-auto object-contain"
              onError={(e: any) => { e.target.style.display = 'none'; }}
            />
            <h1 className="text-xl font-bold tracking-wider">MAQ GESTÃO</h1>
          </div>

          {/* Seletor de Ano do Exercício */}
          <div className="mb-6 bg-slate-800 p-3 rounded-lg border border-slate-700">
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-1 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-blue-400" />
              Ano do Exercício (LNT)
            </label>
            <select 
              value={selectedAno} 
              onChange={(e) => setSelectedAno(Number(e.target.value))}
              className="w-full bg-slate-900 border border-slate-600 rounded px-2.5 py-1.5 text-sm font-bold text-white outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={2026}>Exercício 2026</option>
              <option value={2025}>Exercício 2025</option>
              <option value={2024}>Exercício 2024</option>
              <option value={2023}>Exercício 2023</option>
            </select>
          </div>

          <nav className="space-y-2">
            <button 
              onClick={() => setActiveTab('dashboard')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <BarChart className="w-5 h-5" /> Dashboard Executivo
            </button>
            <button 
              onClick={() => setActiveTab('colaborador')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'colaborador' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <Users className="w-5 h-5" /> Lançamentos
            </button>
            <button 
              onClick={() => setActiveTab('matriz_lnt')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'matriz_lnt' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <Layers className="w-5 h-5" /> Matriz LNT por Cargo
            </button>
            <button 
              onClick={() => setActiveTab('cadastro_colab')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'cadastro_colab' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <Plus className="w-5 h-5" /> Cadastrar Colaborador
            </button>
            <button 
              onClick={() => setActiveTab('catalogo')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'catalogo' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <BookOpen className="w-5 h-5" /> Catálogo Treinamentos
            </button>
            <button 
              onClick={() => setActiveTab('gestao_usuarios')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'gestao_usuarios' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <UserPlus className="w-5 h-5" /> Gestão de Utilizadores
            </button>
          </nav>
        </div>

        <div className="space-y-3">
          <button onClick={() => window.print()} className="w-full flex items-center gap-2 text-slate-400 hover:text-white text-sm transition">
            <Printer className="w-4 h-4" /> Imprimir Relatório
          </button>
          <button onClick={handleLogout} className="w-full flex items-center gap-2 text-red-400 hover:text-red-300 text-sm transition">
            <LogOut className="w-4 h-4" /> Sair da Conta
          </button>
        </div>
      </aside>

      {/* Conteúdo Central */}
      <main className="flex-1 overflow-y-auto p-8">
        
        {/* 1. DASHBOARD EXECUTIVO */}
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            <header className="flex justify-between items-center border-b pb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Dashboard Executivo — Exercício {selectedAno}</h2>
                <p className="text-slate-500 text-sm">Visão consolidada do ano selecionado via Supabase PostgreSQL</p>
              </div>
            </header>

            <div className="grid grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 text-sm font-medium">Total Colaboradores</p>
                <h3 className="text-3xl font-extrabold text-slate-900 mt-2">{colaboradores.length}</h3>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 text-sm font-medium">Horas de Treinamento ({selectedAno})</p>
                <h3 className="text-3xl font-extrabold text-blue-600 mt-2">{totalHoras}h</h3>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 text-sm font-medium">Conclusões Registradas</p>
                <h3 className="text-3xl font-extrabold text-emerald-600 mt-2">{totalConcluidos}</h3>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 text-sm font-medium">Requisitos na Matriz LNT</p>
                <h3 className="text-3xl font-extrabold text-amber-500 mt-2">{matrizLnt.length}</h3>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-8">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h4 className="text-lg font-bold text-slate-800 mb-4">Compliance da Matriz LNT — {selectedAno}</h4>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={statusData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} dataKey="value">
                        {statusData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h4 className="text-lg font-bold text-slate-800 mb-4">Carga Horária por Treinamento</h4>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={treinamentos}>
                      <XAxis dataKey="nome_curso" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="carga_horaria" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 2. LANÇAMENTO POR COLABORADOR */}
        {activeTab === 'colaborador' && (
          <div className="space-y-6">
            <header className="flex justify-between items-center border-b pb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Lançamentos e Histórico Individual — {selectedAno}</h2>
                <p className="text-slate-500 text-sm">Gerencie conclusões, datas e faça o upload de listas de presença em PDF</p>
              </div>

              <div className="flex gap-4">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                  <input 
                    type="text" 
                    placeholder="Filtrar colaborador..." 
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9 pr-4 py-2 border rounded-lg text-sm bg-white shadow-sm outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <select 
                  value={selectedColab} 
                  onChange={(e) => setSelectedColab(e.target.value)}
                  className="px-4 py-2 bg-white border border-slate-300 rounded-lg shadow-sm font-semibold text-slate-700 outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {filteredColaboradores.map(c => (
                    <option key={c.id} value={c.id}>{c.nome} ({c.cargo})</option>
                  ))}
                </select>
              </div>
            </header>

            {currentColabData && (
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
            )}

            {requisitosCargo.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl text-amber-800 text-sm flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <div>
                  <strong>Requisitos Obrigatórios para o cargo ({currentColabData?.cargo}):</strong>
                  <span className="ml-2">{requisitosCargo.map(r => r.treinamentos?.nome_curso).join(', ')}</span>
                </div>
              </div>
            )}

            <div className="space-y-4 mt-6">
              {treinamentos.map(treino => {
                const reg = colabRegistros.find(r => r.treinamento_id === treino.id);
                const isConcluidoBD = !!reg;
                const isObrigatorioCargo = requisitosCargo.some(r => r.treinamento_id === treino.id);

                return (
                  <div key={`${selectedColab}_${treino.id}_${selectedAno}`} className={`bg-white p-6 rounded-xl border ${isObrigatorioCargo ? 'border-l-4 border-l-blue-500 border-slate-200' : 'border-slate-200'} shadow-sm flex items-center justify-between gap-6`}>
                    <div className="w-1/3">
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-slate-900 text-lg">{treino.nome_curso}</h4>
                        {isObrigatorioCargo && (
                          <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded font-semibold">LNT Obrigatória</span>
                        )}
                      </div>
                      <p className="text-slate-500 text-sm">{treino.carga_horaria}h — {treino.classificacao}</p>
                      {reg?.url_forms && (
                        <a href={reg.url_forms} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-2 font-medium">
                          <ExternalLink className="w-3 h-3" /> Ver Evidência Anexada
                        </a>
                      )}
                    </div>

                    <form 
                      onSubmit={(e: any) => {
                        e.preventDefault();
                        const statusVal = e.target.statusSelect.value;
                        const dataVal = e.target.dataInput.value;
                        const aplicadorVal = e.target.aplicadorInput.value;
                        const cargoVal = e.target.cargoInput.value;
                        const file = e.target.arquivoInput.files[0] || null;
                        handleSalvarRegistroDirect(treino.id, statusVal, dataVal, aplicadorVal, cargoVal, file);
                      }}
                      className="flex-1 flex items-center gap-3"
                    >
                      <select 
                        name="statusSelect"
                        value={isConcluidoBD ? '🟢 Concluído' : '🔴 Pendente'} 
                        onChange={(e) => {
                          const novoStatus = e.target.value;
                          const form = e.target.form as any;
                          const dataVal = form.dataInput.value;
                          const aplicadorVal = form.aplicadorInput.value;
                          const cargoVal = form.cargoInput.value;
                          const file = form.arquivoInput.files[0] || null;
                          handleSalvarRegistroDirect(treino.id, novoStatus, dataVal, aplicadorVal, cargoVal, file);
                        }}
                        className={`px-3 py-2 border rounded-lg text-sm font-semibold cursor-pointer ${isConcluidoBD ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-red-50 text-red-700 border-red-300'}`}
                      >
                        <option value="🔴 Pendente">🔴 Pendente</option>
                        <option value="🟢 Concluído">🟢 Concluído</option>
                      </select>

                      <input 
                        name="dataInput"
                        type="date" 
                        defaultValue={reg?.data_realizacao || `${selectedAno}-01-01`} 
                        className="px-3 py-2 border rounded-lg text-sm bg-slate-50" 
                      />
                      
                      <input 
                        name="aplicadorInput"
                        type="text" 
                        defaultValue={reg?.instrutor_nome || treino.aplicador_padrao || ''} 
                        placeholder="Instrutor" 
                        className="px-3 py-2 border rounded-lg text-sm w-36 bg-slate-50" 
                      />

                      <input 
                        name="cargoInput"
                        type="text" 
                        defaultValue={reg?.aplicador_cargo || treino.aplicador_cargo_padrao || ''} 
                        placeholder="Cargo Instrutor" 
                        className="px-3 py-2 border rounded-lg text-sm w-32 bg-slate-50" 
                      />

                      <input name="arquivoInput" type="file" className="text-xs w-36" />

                      <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition shadow-sm">
                        <Save className="w-4 h-4" /> Salvar
                      </button>
                    </form>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 3. MATRIZ LNT POR CARGO */}
        {activeTab === 'matriz_lnt' && (
          <div className="space-y-6">
            <header className="border-b pb-4">
              <h2 className="text-2xl font-bold text-slate-900">Matriz LNT (Levantamento de Necessidades de Treinamento)</h2>
              <p className="text-slate-500 text-sm">Associe treinamentos e normas obrigatórias aos cargos existentes</p>
            </header>

            <form onSubmit={handleAddMatriz} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex gap-4 items-end max-w-3xl">
              <div className="flex-1">
                <label className="block text-xs font-medium text-slate-700 mb-1">Cargo</label>
                <select 
                  value={novaMatriz.cargo} 
                  onChange={e => setNovaMatriz({...novaMatriz, cargo: e.target.value})}
                  className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                  required
                >
                  <option value="">Selecione o cargo...</option>
                  {cargosExistentes.map(cargo => (
                    <option key={cargo} value={cargo}>{cargo}</option>
                  ))}
                </select>
              </div>

              <div className="flex-1">
                <label className="block text-xs font-medium text-slate-700 mb-1">Treinamento Requerido</label>
                <select 
                  value={novaMatriz.treinamento_id} 
                  onChange={e => setNovaMatriz({...novaMatriz, treinamento_id: e.target.value})}
                  className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                  required
                >
                  <option value="">Selecione o curso...</option>
                  {treinamentos.map(t => (
                    <option key={t.id} value={t.id}>{t.nome_curso}</option>
                  ))}
                </select>
              </div>

              <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-semibold text-sm flex items-center gap-2">
                <Plus className="w-4 h-4" /> Vincular LNT
              </button>
            </form>

            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 text-xs uppercase font-semibold">
                  <tr>
                    <th className="p-4">Cargo / Função</th>
                    <th className="p-4">Treinamento Requerido</th>
                    <th className="p-4 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {matrizLnt.map(m => (
                    <tr key={m.id} className="hover:bg-slate-50 transition">
                      <td className="p-4 font-bold text-slate-900">{m.cargo}</td>
                      <td className="p-4 text-blue-600 font-medium">{m.treinamentos?.nome_curso}</td>
                      <td className="p-4 text-right">
                        <button onClick={() => handleDeleteMatrizItem(m.id)} className="text-red-500 hover:text-red-700 transition p-1">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 4. CADASTRO DE COLABORADORES */}
        {activeTab === 'cadastro_colab' && (
          <div className="space-y-6">
            <header className="border-b pb-4">
              <h2 className="text-2xl font-bold text-slate-900">Novo Colaborador</h2>
              <p className="text-slate-500 text-sm">Adicionar funcionários à base corporativa do Supabase</p>
            </header>

            <form onSubmit={handleAddColaborador} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm max-w-2xl space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Nome Completo</label>
                <input type="text" value={novoColab.nome} onChange={e => setNovoColab({...novoColab, nome: e.target.value})} className="w-full p-2 border rounded-lg bg-slate-50" required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Cargo</label>
                  <input type="text" value={novoColab.cargo} onChange={e => setNovoColab({...novoColab, cargo: e.target.value})} className="w-full p-2 border rounded-lg bg-slate-50" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Departamento / Setor</label>
                  <input type="text" value={novoColab.departamento} onChange={e => setNovoColab({...novoColab, departamento: e.target.value})} className="w-full p-2 border rounded-lg bg-slate-50" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Gestor Direto</label>
                <input type="text" value={novoColab.gestor} onChange={e => setNovoColab({...novoColab, gestor: e.target.value})} className="w-full p-2 border rounded-lg bg-slate-50" />
              </div>

              <button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-lg font-semibold flex items-center gap-2">
                <Plus className="w-5 h-5" /> Cadastrar Colaborador
              </button>
            </form>
          </div>
        )}

        {/* 5. CATÁLOGO DE TREINAMENTOS */}
        {activeTab === 'catalogo' && (
          <div className="space-y-6">
            <header className="border-b pb-4">
              <h2 className="text-2xl font-bold text-slate-900">Catálogo Geral de Treinamentos</h2>
              <p className="text-slate-500 text-sm">Cursos, procedimentos operacionais (PO/IT) e normas regulamentadoras</p>
            </header>

            <form onSubmit={handleAddTreinamento} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm grid grid-cols-5 gap-4 items-end">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Nome / Norma</label>
                <input type="text" value={novoTreino.nome_curso} onChange={e => setNovoTreino({...novoTreino, nome_curso: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" required />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Carga Horária (h)</label>
                <input type="number" step="0.5" value={novoTreino.carga_horaria} onChange={e => setNovoTreino({...novoTreino, carga_horaria: parseFloat(e.target.value)})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Frequência</label>
                <input type="text" value={novoTreino.frequencia} onChange={e => setNovoTreino({...novoTreino, frequencia: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Classificação</label>
                <input type="text" value={novoTreino.classificacao} onChange={e => setNovoTreino({...novoTreino, classificacao: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" />
              </div>
              <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2">
                <Plus className="w-4 h-4" /> Criar Curso
              </button>
            </form>

            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 text-xs uppercase font-semibold">
                  <tr>
                    <th className="p-4">Treinamento / Norma</th>
                    <th className="p-4">Carga Horária</th>
                    <th className="p-4">Frequência</th>
                    <th className="p-4">Classificação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {treinamentos.map(t => (
                    <tr key={t.id} className="hover:bg-slate-50 transition">
                      <td className="p-4 font-bold text-slate-900">{t.nome_curso}</td>
                      <td className="p-4">{t.carga_horaria} horas</td>
                      <td className="p-4">{t.frequencia}</td>
                      <td className="p-4">{t.classificacao}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 6. GESTÃO DE UTILIZADORES DO SISTEMA */}
        {activeTab === 'gestao_usuarios' && (
          <div className="space-y-6">
            <header className="border-b pb-4">
              <h2 className="text-2xl font-bold text-slate-900">Gestão de Utilizadores e Acessos</h2>
              <p className="text-slate-500 text-sm">Crie novas contas de acesso para outros administradores ou técnicos</p>
            </header>

            <form onSubmit={handleCreateUser} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm max-w-md space-y-4">
              {userSuccess && (
                <div className="bg-emerald-50 text-emerald-700 p-3 rounded-lg text-xs font-semibold border border-emerald-200">
                  {userSuccess}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Novo E-mail</label>
                <input 
                  type="email" 
                  value={novoUsuario.email} 
                  onChange={e => setNovoUsuario({...novoUsuario, email: e.target.value})} 
                  placeholder="novo_usuario@attendambiental.com.br"
                  className="w-full p-2 border rounded-lg text-sm bg-slate-50" 
                  required 
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Senha Provisória</label>
                <input 
                  type="password" 
                  value={novoUsuario.password} 
                  onChange={e => setNovoUsuario({...novoUsuario, password: e.target.value})} 
                  placeholder="••••••••"
                  className="w-full p-2 border rounded-lg text-sm bg-slate-50" 
                  required 
                />
              </div>

              <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2">
                <UserPlus className="w-4 h-4" /> Criar Novo Acesso
              </button>
            </form>
          </div>
        )}

      </main>
    </div>
  );
}